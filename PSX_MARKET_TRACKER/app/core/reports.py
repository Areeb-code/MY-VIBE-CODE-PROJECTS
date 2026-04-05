# ═══════════════════════════════════════════════════════════════════════════════
# PROFESSIONAL REPORT GENERATOR — Financial-Grade PDF & Excel Exports
# ═══════════════════════════════════════════════════════════════════════════════
import os
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


# ─── Color Palette ─────────────────────────────────────────────────────────────
class Colors:
    """Financial Dark theme palette."""
    NAVY       = (15, 23, 42)      # Deep navy background
    CHARCOAL   = (30, 41, 59)      # Section headers
    SLATE      = (51, 65, 85)      # Subtle borders
    WHITE      = (255, 255, 255)
    LIGHT_GRAY = (241, 245, 249)   # Zebra even rows
    MID_GRAY   = (226, 232, 240)   # Table borders
    EMERALD    = (16, 185, 129)    # Brand / Profit
    RED        = (239, 68, 68)     # Loss
    GOLD       = (245, 158, 11)    # Accent / Badge
    MUTED      = (148, 163, 184)   # Secondary text


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
class PDFReportGenerator:
    """Generates a multi-page, financial-grade PDF report."""

    ROW_H = 8    # Row height in mm
    PAD   = 10   # Page margins

    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager

    def generate_report(self, file_path, transactions, aggregated_portfolio, live_data=None):
        if not FPDF:
            raise ImportError("fpdf2 is not installed. Run: pip install fpdf2")

        self.live_data = live_data or {}
        self.agg = aggregated_portfolio
        self.tx_rows = self._prepare_log_data(transactions)
        self.monthly = self._prepare_monthly_data(transactions)
        self._calc_metrics()

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_title("PSX Market Tracker — Financial Report")
        pdf.set_author("PSX Tracker")

        # ── Page 1: Executive Dashboard ──
        self._render_executive_dashboard(pdf)

        # ── Page 2: Active Portfolio ──
        self._render_active_portfolio(pdf)

        # ── Page 3+: Transaction Log ──
        self._render_transaction_log(pdf)

        # ── Page N: Monthly Performance ──
        self._render_monthly_performance(pdf)

        pdf.output(file_path)

    # ─── DATA PREPARATION ──────────────────────────────────────────────────
    def _prepare_log_data(self, transactions):
        sorted_tx = sorted(transactions, key=lambda x: x['date'])
        state = {}
        rows = []
        running_cash = 0.0

        for t in sorted_tx:
            sym, qty, price, type_ = t['symbol'], t['quantity'], t['price'], t['type']
            total = qty * price

            if sym not in state:
                state[sym] = {"qty": 0, "avg": 0.0}
            s = state[sym]

            pl = None
            if type_ == "BUY":
                new_cost = qty * price
                total_val = (s['qty'] * s['avg']) + new_cost
                new_qty = s['qty'] + qty
                s['avg'] = total_val / new_qty if new_qty > 0 else 0
                s['qty'] = new_qty
                running_cash -= total
                desc = f"Buy {sym}"
            else:
                pl = (price - s['avg']) * qty
                s['qty'] = max(0, s['qty'] - qty)
                running_cash += total
                desc = f"Sell {sym}"

            rows.append({
                "date": t['date'], "type": type_, "symbol": sym,
                "desc": desc, "qty": qty, "price": price,
                "total": total, "pl": pl, "cash": running_cash
            })
        return rows

    def _prepare_monthly_data(self, transactions):
        if not transactions:
            return []
        sorted_tx = sorted(transactions, key=lambda x: x['date'])
        monthly = defaultdict(lambda: {"invested": 0.0, "sold": 0.0, "buys": 0, "sells": 0})

        for t in sorted_tx:
            try:
                dt = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
            except:
                dt = datetime.now()
            key = dt.strftime("%Y-%m")
            if t['type'] == "BUY":
                monthly[key]["invested"] += t['quantity'] * t['price']
                monthly[key]["buys"] += 1
            else:
                monthly[key]["sold"] += t['quantity'] * t['price']
                monthly[key]["sells"] += 1

        result = []
        cumulative_invested = 0.0
        cumulative_sold = 0.0
        for month_key in sorted(monthly.keys()):
            m = monthly[month_key]
            cumulative_invested += m["invested"]
            cumulative_sold += m["sold"]
            net = cumulative_sold - cumulative_invested
            growth = (net / cumulative_invested * 100) if cumulative_invested > 0 else 0
            result.append({
                "month": month_key,
                "cash_injected": m["invested"],
                "value_end": cumulative_sold,
                "cumulative_invested": cumulative_invested,
                "growth_pct": growth,
                "buys": m["buys"],
                "sells": m["sells"]
            })
        return result

    def _calc_metrics(self):
        self.total_invested = sum(
            info['quantity'] * info['buy_price'] for info in self.agg.values()
        )
        self.total_current = sum(
            info['quantity'] * self.live_data.get(sym, info['buy_price'])
            for sym, info in self.agg.items()
        )
        self.unrealized_pl = self.total_current - self.total_invested
        self.realized_pl = sum(r['pl'] for r in self.tx_rows if r['pl'] is not None)

        # Annualized return
        if self.tx_rows:
            try:
                start = datetime.strptime(self.tx_rows[0]['date'], "%Y-%m-%d %H:%M:%S")
            except:
                start = datetime.now()
        else:
            start = datetime.now()
        days = max(1, (datetime.now() - start).days)
        roi = (self.realized_pl / self.total_invested * 100) if self.total_invested > 0 else 0
        self.annualized = roi * (365 / days)
        self.days_active = days

    # ─── HELPERS ───────────────────────────────────────────────────────────
    def _user_name(self):
        if self.settings_manager:
            return self.settings_manager.get("user_name") or "Investor"
        return "Investor"

    def _draw_header_bar(self, pdf, title, subtitle=""):
        """Dark charcoal header bar with white text."""
        pdf.set_fill_color(*Colors.CHARCOAL)
        pdf.rect(0, 0, 210, 38, 'F')

        # Logo
        if self.settings_manager:
            lp = self.settings_manager.get("user_logo_path")
            if lp and os.path.exists(lp):
                try:
                    pdf.image(lp, 10, 5, 28)
                except:
                    pass

        x_off = 45 if (self.settings_manager and self.settings_manager.get("user_logo_path")) else 10

        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*Colors.WHITE)
        pdf.set_xy(x_off, 8)
        pdf.cell(0, 10, title, align="L")

        if subtitle:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*Colors.MUTED)
            pdf.set_xy(x_off, 20)
            pdf.cell(0, 8, subtitle, align="L")

    def _draw_card(self, pdf, x, y, w, h, label, value, color=Colors.WHITE, badge=False):
        """Draws a summary card with rounded-ish feel."""
        # Card background
        pdf.set_fill_color(*Colors.CHARCOAL)
        pdf.rect(x, y, w, h, 'F')

        # Accent line at top
        pdf.set_fill_color(*color)
        pdf.rect(x, y, w, 2.5, 'F')

        # Label
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*Colors.MUTED)
        pdf.set_xy(x + 5, y + 6)
        pdf.cell(w - 10, 5, label, align="L")

        # Value
        if badge:
            pdf.set_font("Helvetica", "B", 20)
        else:
            pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*color)
        pdf.set_xy(x + 5, y + 14)
        pdf.cell(w - 10, 10, str(value), align="L")

    def _table_header(self, pdf, headers, widths, y_start=None):
        """Renders a professional table header row."""
        if y_start:
            pdf.set_xy(self.PAD, y_start)
        pdf.set_fill_color(*Colors.CHARCOAL)
        pdf.set_text_color(*Colors.WHITE)
        pdf.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], self.ROW_H, h, border=0, fill=True, align='C')
        pdf.ln()

    def _table_row(self, pdf, cells, widths, row_idx, aligns=None):
        """Renders a data row with zebra striping."""
        if row_idx % 2 == 0:
            pdf.set_fill_color(*Colors.LIGHT_GRAY)
        else:
            pdf.set_fill_color(*Colors.WHITE)
        pdf.set_text_color(*Colors.NAVY)
        pdf.set_font("Helvetica", "", 8)

        if not aligns:
            aligns = ['C'] * len(cells)

        for i, c in enumerate(cells):
            pdf.cell(widths[i], self.ROW_H, str(c), border=0, fill=True, align=aligns[i])
        pdf.ln()

    # ════════════════════════════════════════════════════════════════════════
    #  PAGE 1: EXECUTIVE DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    def _render_executive_dashboard(self, pdf):
        pdf.add_page()
        self._draw_header_bar(pdf, "PSX Market Tracker", f"Prepared for {self._user_name()}")

        # Report Date
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*Colors.MUTED)
        pdf.set_xy(self.PAD, 42)
        pdf.cell(0, 6, f"Report Date: {datetime.now().strftime('%B %d, %Y')}  |  Days Active: {self.days_active}", align="L")

        # ── 3 Summary Cards ──
        card_y = 54
        card_w = 60
        card_h = 32
        gap = 5
        total_w = card_w * 3 + gap * 2
        start_x = (210 - total_w) / 2

        # Card 1: Total Capital Invested
        self._draw_card(pdf, start_x, card_y, card_w, card_h,
                        "TOTAL CAPITAL INVESTED",
                        f"Rs. {self.total_invested:,.0f}",
                        Colors.WHITE)

        # Card 2: Current Market Value
        self._draw_card(pdf, start_x + card_w + gap, card_y, card_w, card_h,
                        "CURRENT MARKET VALUE",
                        f"Rs. {self.total_current:,.0f}",
                        Colors.EMERALD)

        # Card 3: Net Profit/Loss
        pl_color = Colors.EMERALD if self.unrealized_pl >= 0 else Colors.RED
        pl_pct = (self.unrealized_pl / self.total_invested * 100) if self.total_invested > 0 else 0
        self._draw_card(pdf, start_x + 2 * (card_w + gap), card_y, card_w, card_h,
                        "NET PROFIT / LOSS",
                        f"Rs. {self.unrealized_pl:+,.0f}  ({pl_pct:+.1f}%)",
                        pl_color)

        # ── Annualized Return Badge ──
        badge_y = card_y + card_h + 10
        badge_w = 90
        badge_h = 28
        badge_x = (210 - badge_w) / 2

        # Badge background
        pdf.set_fill_color(*Colors.NAVY)
        pdf.rect(badge_x, badge_y, badge_w, badge_h, 'F')
        # Gold accent
        pdf.set_fill_color(*Colors.GOLD)
        pdf.rect(badge_x, badge_y, badge_w, 3, 'F')

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*Colors.MUTED)
        pdf.set_xy(badge_x, badge_y + 5)
        pdf.cell(badge_w, 5, "ANNUALIZED RETURN", align="C")

        ann_color = Colors.EMERALD if self.annualized >= 0 else Colors.RED
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*ann_color)
        pdf.set_xy(badge_x, badge_y + 12)
        pdf.cell(badge_w, 12, f"{self.annualized:+.2f}%", align="C")

        # ── Quick Stats Table ──
        stats_y = badge_y + badge_h + 12
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*Colors.NAVY)
        pdf.set_xy(self.PAD, stats_y)
        pdf.cell(0, 8, "Quick Statistics", ln=True)
        stats_y += 10

        stats = [
            ("Total Buy Transactions", str(sum(1 for r in self.tx_rows if r['type'] == 'BUY'))),
            ("Total Sell Transactions", str(sum(1 for r in self.tx_rows if r['type'] == 'SELL'))),
            ("Realized P/L", f"Rs. {self.realized_pl:+,.2f}"),
            ("Unrealized P/L", f"Rs. {self.unrealized_pl:+,.2f}"),
            ("Unique Symbols Traded", str(len(self.agg))),
            ("Active Holdings", str(sum(1 for info in self.agg.values() if info['quantity'] > 0))),
        ]

        headers = ["Metric", "Value"]
        widths = [95, 95]
        self._table_header(pdf, headers, widths, stats_y)

        for idx, (metric, val) in enumerate(stats):
            self._table_row(pdf, [metric, val], widths, idx, ['L', 'R'])

    # ════════════════════════════════════════════════════════════════════════
    #  PAGE 2: ACTIVE PORTFOLIO
    # ════════════════════════════════════════════════════════════════════════
    def _render_active_portfolio(self, pdf):
        pdf.add_page()
        self._draw_header_bar(pdf, "Active Portfolio", "Current Holdings Summary")

        pdf.set_xy(self.PAD, 44)

        headers = ["Symbol", "Qty", "WAC (Avg Cost)", "Market Price", "Invested", "Market Value", "Unrealized P/L"]
        widths = [24, 16, 28, 28, 28, 28, 38]
        self._table_header(pdf, headers, widths)

        row_idx = 0
        for sym, info in self.agg.items():
            if info['quantity'] <= 0:
                continue
            qty = info['quantity']
            wac = info['buy_price']
            curr = self.live_data.get(sym, wac)
            invested = qty * wac
            mkt_val = qty * curr
            upl = mkt_val - invested

            # Color the P/L
            cells = [
                sym, str(qty), f"{wac:,.2f}", f"{curr:,.2f}",
                f"{invested:,.0f}", f"{mkt_val:,.0f}", f"{upl:+,.0f}"
            ]
            aligns = ['C', 'C', 'R', 'R', 'R', 'R', 'R']

            # Custom row to color P/L cell
            if row_idx % 2 == 0:
                pdf.set_fill_color(*Colors.LIGHT_GRAY)
            else:
                pdf.set_fill_color(*Colors.WHITE)

            pdf.set_font("Helvetica", "", 8)
            for i, c in enumerate(cells):
                if i == 6:  # P/L column
                    if upl >= 0:
                        pdf.set_text_color(*Colors.EMERALD)
                    else:
                        pdf.set_text_color(*Colors.RED)
                else:
                    pdf.set_text_color(*Colors.NAVY)
                pdf.cell(widths[i], self.ROW_H, c, border=0, fill=True, align=aligns[i])
            pdf.ln()
            row_idx += 1

        if row_idx == 0:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(*Colors.MUTED)
            pdf.cell(sum(widths), 12, "No active holdings.", align="C")

    # ════════════════════════════════════════════════════════════════════════
    #  PAGE 3+: TRANSACTION LOG (repeating headers)
    # ════════════════════════════════════════════════════════════════════════
    def _render_transaction_log(self, pdf):
        pdf.add_page()
        self._draw_header_bar(pdf, "Transaction Log", f"{len(self.tx_rows)} entries")

        headers = ["Date", "Description", "Symbol", "Rate", "Qty", "Total", "Cash Balance"]
        widths = [32, 28, 20, 24, 18, 28, 40]

        pdf.set_xy(self.PAD, 44)
        self._table_header(pdf, headers, widths)

        rows_desc = list(reversed(self.tx_rows))  # newest first

        for idx, r in enumerate(rows_desc):
            # Check if we need a new page
            if pdf.get_y() > 270:
                pdf.add_page()
                pdf.set_xy(self.PAD, 12)
                # Continuation header
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(*Colors.MUTED)
                pdf.cell(0, 6, f"Transaction Log (Continued) — Page {pdf.page_no()}", ln=True)
                pdf.ln(2)
                self._table_header(pdf, headers, widths)

            # Format cells
            try:
                dt = datetime.strptime(r['date'], "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
            except:
                date_str = str(r['date'])[:10]

            cash_str = f"Rs. {r['cash']:+,.0f}"

            cells = [
                date_str, r['desc'], r['symbol'],
                f"{r['price']:,.2f}", str(r['qty']),
                f"{r['total']:,.0f}", cash_str
            ]
            aligns = ['C', 'L', 'C', 'R', 'C', 'R', 'R']

            # Row with type-colored description
            if idx % 2 == 0:
                pdf.set_fill_color(*Colors.LIGHT_GRAY)
            else:
                pdf.set_fill_color(*Colors.WHITE)
            pdf.set_font("Helvetica", "", 8)

            for i, c in enumerate(cells):
                if i == 1:  # Description
                    if r['type'] == 'BUY':
                        pdf.set_text_color(*Colors.EMERALD)
                    else:
                        pdf.set_text_color(*Colors.RED)
                else:
                    pdf.set_text_color(*Colors.NAVY)
                pdf.cell(widths[i], self.ROW_H, c, border=0, fill=True, align=aligns[i])
            pdf.ln()

    # ════════════════════════════════════════════════════════════════════════
    #  PAGE N: MONTHLY PERFORMANCE LOG
    # ════════════════════════════════════════════════════════════════════════
    def _render_monthly_performance(self, pdf):
        pdf.add_page()

        if self.days_active >= 30 and len(self.monthly) > 0:
            self._draw_header_bar(pdf, "Monthly Performance", "Growth Analysis by Month")

            headers = ["Month", "Cash Injected", "Cumul. Invested", "Buys", "Sells", "Growth %"]
            widths = [30, 30, 32, 20, 20, 28]
            total_w = sum(widths)
            start_x = (210 - total_w) / 2

            pdf.set_xy(start_x, 44)
            self._table_header(pdf, headers, widths)

            for idx, m in enumerate(self.monthly):
                growth_str = f"{m['growth_pct']:+.2f}%"
                cells = [
                    m['month'],
                    f"Rs. {m['cash_injected']:,.0f}",
                    f"Rs. {m['cumulative_invested']:,.0f}",
                    str(m['buys']),
                    str(m['sells']),
                    growth_str
                ]
                aligns = ['C', 'R', 'R', 'C', 'C', 'R']

                if idx % 2 == 0:
                    pdf.set_fill_color(*Colors.LIGHT_GRAY)
                else:
                    pdf.set_fill_color(*Colors.WHITE)
                pdf.set_font("Helvetica", "", 8)

                for i, c in enumerate(cells):
                    if i == 5:  # Growth %
                        if m['growth_pct'] >= 0:
                            pdf.set_text_color(*Colors.EMERALD)
                        else:
                            pdf.set_text_color(*Colors.RED)
                    else:
                        pdf.set_text_color(*Colors.NAVY)
                    pdf.cell(widths[i], self.ROW_H, c, border=0, fill=True, align=aligns[i])
                pdf.ln()
        else:
            # Growth Projection for new users
            self._draw_header_bar(pdf, "Growth Projection", "Based on Current Week's Performance")

            pdf.set_xy(self.PAD, 50)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(*Colors.NAVY)
            pdf.multi_cell(190, 7,
                "Your portfolio is less than 30 days old. "
                "Once you have a full month of activity, this page will show "
                "a detailed monthly performance breakdown.\n\n"
                "Here's a projection based on your current activity:"
            )

            pdf.ln(5)

            # Simple projection
            if self.days_active > 0 and self.total_invested > 0:
                daily_return = self.realized_pl / self.days_active
                weekly = daily_return * 7
                monthly_proj = daily_return * 30
                yearly_proj = daily_return * 365

                proj_data = [
                    ("Current Daily Return", f"Rs. {daily_return:+,.2f}"),
                    ("Projected Weekly", f"Rs. {weekly:+,.2f}"),
                    ("Projected Monthly", f"Rs. {monthly_proj:+,.2f}"),
                    ("Projected Yearly", f"Rs. {yearly_proj:+,.2f}"),
                ]

                headers = ["Projection", "Estimated Value"]
                widths = [95, 95]
                self._table_header(pdf, headers, widths)

                for idx, (label, val) in enumerate(proj_data):
                    self._table_row(pdf, [label, val], widths, idx, ['L', 'R'])


# ═══════════════════════════════════════════════════════════════════════════════
#  EXCEL REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
class ExcelReportGenerator:
    """Generates a multi-sheet, professionally styled Excel workbook."""

    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager

    def generate_report(self, file_path, transactions, aggregated_portfolio, live_data=None):
        import pandas as pd

        self.live_data = live_data or {}
        self.agg = aggregated_portfolio
        self.transactions = transactions
        
        # Prepare metrics (matching PDF logic)
        self._prepare_log_data(transactions)
        self._calc_metrics()

        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        workbook = writer.book

        # ── Shared Formats ──
        fmt = self._create_formats(workbook)

        # ── Sheet 1: Executive Dashboard ──
        self._write_dashboard_sheet(writer, workbook, fmt)

        # ── Sheet 2: Active Portfolio ──
        self._write_portfolio_sheet(writer, workbook, fmt)

        # ── Sheet 3: Transaction Log ──
        self._write_log_sheet(writer, workbook, fmt)

        # ── Sheet 4: Monthly Performance ──
        self._write_monthly_sheet(writer, workbook, fmt)

        writer.close()

    def _prepare_log_data(self, transactions):
        """Prepares transaction rows with P/L info (Shared logic)."""
        self.tx_rows = []
        state = {}
        for t in sorted(transactions, key=lambda x: x['date']):
            sym = t['symbol']
            if sym not in state: state[sym] = {"qty": 0, "avg": 0.0}
            s = state[sym]
            
            pl = None
            if t['type'] == "SELL":
                pl = (t['price'] - s['avg']) * t['quantity']
                s['qty'] = max(0, s['qty'] - t['quantity'])
            else:
                new_qty = s['qty'] + t['quantity']
                new_avg = ((s['qty'] * s['avg']) + (t['quantity'] * t['price'])) / new_qty if new_qty > 0 else 0
                s['avg'] = new_avg
                s['qty'] = new_qty
            
            self.tx_rows.append({
                'date': t['date'],
                'type': t['type'],
                'symbol': sym,
                'price': t['price'],
                'qty': t['quantity'],
                'total': t['quantity'] * t['price'],
                'pl': pl
            })

    def _calc_metrics(self):
        """Calculates dashboard metrics (Shared logic)."""
        self.total_invested = sum(info['quantity'] * info['buy_price'] for info in self.agg.values())
        self.total_current = sum(info['quantity'] * self.live_data.get(sym, info['buy_price']) for sym, info in self.agg.items())
        self.net_pl = self.total_current - self.total_invested
        self.realized_pl = sum(r['pl'] for r in self.tx_rows if r['pl'] is not None)
        
        # Annualized
        if self.tx_rows:
            try: start = datetime.strptime(self.tx_rows[0]['date'], "%Y-%m-%d %H:%M:%S")
            except: start = datetime.now()
        else: start = datetime.now()
        
        days = max(1, (datetime.now() - start).days)
        roi = (self.realized_pl / self.total_invested * 100) if self.total_invested > 0 else 0
        self.annualized = roi * (365 / days)

    def _user_name(self):
        if self.settings_manager:
            return self.settings_manager.get("user_name") or "Investor"
        return "Investor"

    def _create_formats(self, wb):
        """Create all reusable formats for the workbook."""
        f = {}

        # Title
        f['title'] = wb.add_format({
            'bold': True, 'font_size': 20, 'font_color': '#FFFFFF',
            'bg_color': '#1E293B', 'font_name': 'Segoe UI',
            'bottom': 2, 'bottom_color': '#10B981'
        })
        f['subtitle'] = wb.add_format({
            'italic': True, 'font_size': 11, 'font_color': '#94A3B8',
            'bg_color': '#1E293B', 'font_name': 'Segoe UI'
        })

        # Headers
        f['header'] = wb.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1E293B',
            'border': 1, 'border_color': '#334155',
            'align': 'center', 'valign': 'vcenter',
            'font_name': 'Segoe UI', 'font_size': 10,
            'text_wrap': True
        })

        # Data cells
        f['cell'] = wb.add_format({
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'valign': 'vcenter', 'indent': 1
        })
        f['cell_alt'] = wb.add_format({
            'border': 1, 'border_color': '#E2E8F0',
            'bg_color': '#F1F5F9',
            'font_name': 'Segoe UI', 'font_size': 10,
            'valign': 'vcenter', 'indent': 1
        })

        # Money formats
        f['money'] = wb.add_format({
            'num_format': 'Rs #,##0.00', 'border': 1,
            'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'right', 'valign': 'vcenter'
        })
        f['money_alt'] = wb.add_format({
            'num_format': 'Rs #,##0.00', 'border': 1,
            'border_color': '#E2E8F0', 'bg_color': '#F1F5F9',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'right', 'valign': 'vcenter'
        })

        # Profit / Loss
        f['profit'] = wb.add_format({
            'num_format': '+Rs #,##0.00;-Rs #,##0.00',
            'font_color': '#10B981', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'right', 'valign': 'vcenter'
        })
        f['loss'] = wb.add_format({
            'num_format': '+Rs #,##0.00;-Rs #,##0.00',
            'font_color': '#EF4444', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'right', 'valign': 'vcenter'
        })

        # Percent
        f['pct_profit'] = wb.add_format({
            'num_format': '+0.00%;-0.00%',
            'font_color': '#10B981', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })
        f['pct_loss'] = wb.add_format({
            'num_format': '+0.00%;-0.00%',
            'font_color': '#EF4444', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })

        # Card / metric styles
        f['metric_label'] = wb.add_format({
            'font_color': '#94A3B8', 'font_size': 10,
            'bg_color': '#1E293B', 'font_name': 'Segoe UI',
            'valign': 'vcenter', 'indent': 1
        })
        f['metric_value'] = wb.add_format({
            'font_color': '#FFFFFF', 'font_size': 16, 'bold': True,
            'bg_color': '#1E293B', 'font_name': 'Segoe UI',
            'valign': 'vcenter', 'indent': 1
        })
        f['metric_profit'] = wb.add_format({
            'font_color': '#10B981', 'font_size': 16, 'bold': True,
            'bg_color': '#1E293B', 'font_name': 'Segoe UI',
            'valign': 'vcenter', 'indent': 1
        })
        f['metric_loss'] = wb.add_format({
            'font_color': '#EF4444', 'font_size': 16, 'bold': True,
            'bg_color': '#1E293B', 'font_name': 'Segoe UI',
            'valign': 'vcenter', 'indent': 1
        })

        # Buy/Sell type
        f['buy_type'] = wb.add_format({
            'font_color': '#10B981', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })
        f['sell_type'] = wb.add_format({
            'font_color': '#EF4444', 'bold': True,
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })

        # Center cell
        f['center'] = wb.add_format({
            'border': 1, 'border_color': '#E2E8F0',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })
        f['center_alt'] = wb.add_format({
            'border': 1, 'border_color': '#E2E8F0',
            'bg_color': '#F1F5F9',
            'font_name': 'Segoe UI', 'font_size': 10,
            'align': 'center', 'valign': 'vcenter'
        })

        # New: Dash Header Sub-header Style
        f['dash_stats_title'] = wb.add_format({
            'bold': True, 'font_size': 13, 'font_color': '#1E293B',
            'font_name': 'Segoe UI', 'bottom': 1, 'bottom_color': '#10B981'
        })
        
        # New: Annualized Badge Formats
        f['badge_bg'] = wb.add_format({'bg_color': '#1E293B', 'align': 'center'})
        f['badge_label'] = wb.add_format({
            'font_color': '#94A3B8', 'font_size': 9, 'bg_color': '#1E293B',
            'align': 'center', 'font_name': 'Segoe UI'
        })
        f['badge_value_green'] = wb.add_format({
            'font_color': '#10B981', 'font_size': 18, 'bold': True,
            'bg_color': '#1E293B', 'align': 'center', 'font_name': 'Segoe UI'
        })
        f['badge_value_red'] = wb.add_format({
            'font_color': '#EF4444', 'font_size': 18, 'bold': True,
            'bg_color': '#1E293B', 'align': 'center', 'font_name': 'Segoe UI'
        })

        return f

    # ── Sheet 1: Executive Dashboard ──────────────────────────────────────
    def _write_dashboard_sheet(self, writer, wb, f):
        ws = wb.add_worksheet("Dashboard")
        ws.hide_gridlines(2)
        ws.set_tab_color('#10B981')

        ws.set_column('A:A', 3)
        ws.set_column('B:D', 22)
        ws.set_column('E:E', 28) # Badge column

        # Header Area Background (Avoid set_row to prevent style corruption)
        for r in range(8):
            for c in range(6):
                ws.write(r, c, "", wb.add_format({'bg_color': '#1E293B'}))

        ws.set_row(0, 35)
        ws.merge_range('B1:E1', 'PSX Market Tracker — Financial Dashboard', f['title'])
        ws.set_row(1, 20)
        ws.merge_range('B2:E2', f'Prepared for {self._user_name()}  |  {datetime.now().strftime("%B %d, %Y")}', f['subtitle'])

        # Metrics
        ws.set_row(3, 18)
        ws.set_row(4, 30)

        labels = ['TOTAL INVESTED', 'CURRENT VALUE', 'NET P/L']
        values = [f'Rs. {self.total_invested:,.0f}', f'Rs. {self.total_current:,.0f}', f'Rs. {self.net_pl:+,.0f}']
        value_fmts = [f['metric_value'], 
                      f['metric_profit'] if self.total_current >= self.total_invested else f['metric_loss'],
                      f['metric_profit'] if self.net_pl >= 0 else f['metric_loss']]

        cols = ['B', 'C', 'D']
        for i, col in enumerate(cols):
            ws.write(f'{col}4', labels[i], f['metric_label'])
            ws.write(f'{col}5', values[i], value_fmts[i])

        # ── Annualized Return Badge (Column E) ──
        ws.write('E4', 'ANNUALIZED RETURN', f['badge_label'])
        ann_fmt = f['badge_value_green'] if self.annualized >= 0 else f['badge_value_red']
        ws.write('E5', f'{self.annualized:+.2f}%', ann_fmt)

        # Quick stats table
        ws.set_row(7, 18)
        ws.merge_range('B8:C8', 'Quick Statistics', f['dash_stats_title'])

        stats = [
            ("Buy Transactions", sum(1 for r in self.tx_rows if r['type'] == 'BUY')),
            ("Sell Transactions", sum(1 for r in self.tx_rows if r['type'] == 'SELL')),
            ("Realized P/L", f"Rs. {self.realized_pl:+,.2f}"),
            ("Unique Symbols", len(self.agg)),
            ("Active Holdings", sum(1 for info in self.agg.values() if info['quantity'] > 0)),
        ]

        row = 8
        ws.write(row, 1, "Metric", f['header'])
        ws.write(row, 2, "Value", f['header'])
        row += 1

        for idx, (metric, val) in enumerate(stats):
            c = f['cell_alt'] if idx % 2 == 0 else f['cell']
            ws.write(row + idx, 1, metric, c)
            ws.write(row + idx, 2, str(val), c)

    # ── Sheet 2: Active Portfolio ─────────────────────────────────────────
    def _write_portfolio_sheet(self, writer, wb, f):
        ws = wb.add_worksheet("Portfolio")
        ws.hide_gridlines(2)
        ws.set_tab_color('#F59E0B')

        ws.set_row(0, 30)
        ws.merge_range('A1:G1', 'Active Portfolio — Current Holdings', f['title'])

        headers = ["Symbol", "Quantity", "WAC (Avg Cost)", "Market Price", "Invested", "Market Value", "Unrealized P/L"]
        col_widths = [14, 12, 16, 16, 18, 18, 18]

        for i, h in enumerate(headers):
            ws.set_column(i, i, col_widths[i])
            ws.write(2, i, h, f['header'])

        row = 3
        for sym, info in self.agg.items():
            if info['quantity'] <= 0:
                continue
            qty = info['quantity']
            wac = info['buy_price']
            curr = self.live_data.get(sym, wac)
            invested = qty * wac
            mkt_val = qty * curr
            upl = mkt_val - invested
            is_alt = (row - 3) % 2 == 0
            c = f['cell_alt'] if is_alt else f['cell']
            m = f['money_alt'] if is_alt else f['money']

            ws.write(row, 0, sym, f['center_alt'] if is_alt else f['center'])
            ws.write(row, 1, qty, f['center_alt'] if is_alt else f['center'])
            ws.write(row, 2, wac, m)
            ws.write(row, 3, curr, m)
            ws.write(row, 4, invested, m)
            ws.write(row, 5, mkt_val, m)
            ws.write(row, 6, upl, f['profit'] if upl >= 0 else f['loss'])
            row += 1

    # ── Sheet 3: Transaction Log ──────────────────────────────────────────
    def _write_log_sheet(self, writer, wb, f):
        ws = wb.add_worksheet("Transaction Log")
        ws.hide_gridlines(2)
        ws.set_tab_color('#3B82F6')

        ws.set_row(0, 30)
        ws.merge_range('A1:G1', 'Complete Transaction History', f['title'])

        headers = ["Date", "Type", "Symbol", "Rate", "Quantity", "Total Amount", "Running Cash"]
        col_widths = [16, 10, 14, 14, 12, 18, 18]

        for i, h in enumerate(headers):
            ws.set_column(i, i, col_widths[i])
            ws.write(2, i, h, f['header'])

        # Prepare data with running cash
        sorted_tx = sorted(self.transactions, key=lambda x: x['date'], reverse=True)
        # We need running cash, so compute forward then reverse display
        fwd_sorted = sorted(self.transactions, key=lambda x: x['date'])
        cash_map = {}
        cash = 0.0
        for t in fwd_sorted:
            total = t['quantity'] * t['price']
            if t['type'] == 'BUY':
                cash -= total
            else:
                cash += total
            cash_map[t.get('id', '')] = cash

        row = 3
        for t in sorted_tx:
            is_alt = (row - 3) % 2 == 0
            c = f['cell_alt'] if is_alt else f['cell']
            m = f['money_alt'] if is_alt else f['money']
            ct = f['center_alt'] if is_alt else f['center']

            try:
                dt = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
            except:
                date_str = str(t['date'])[:10]

            ws.write(row, 0, date_str, ct)
            ws.write(row, 1, t['type'], f['buy_type'] if t['type'] == 'BUY' else f['sell_type'])
            ws.write(row, 2, t['symbol'], ct)
            ws.write(row, 3, t['price'], m)
            ws.write(row, 4, t['quantity'], ct)
            ws.write(row, 5, t['quantity'] * t['price'], m)
            ws.write(row, 6, cash_map.get(t.get('id', ''), 0), m)
            row += 1

    # ── Sheet 4: Monthly Performance ──────────────────────────────────────
    def _write_monthly_sheet(self, writer, wb, f):
        ws = wb.add_worksheet("Monthly Performance")
        ws.hide_gridlines(2)
        ws.set_tab_color('#EC4899')

        ws.set_row(0, 30)
        ws.merge_range('A1:F1', 'Monthly Performance Analysis', f['title'])

        headers = ["Month", "Cash Injected", "Cumul. Invested", "Buys", "Sells", "Growth %"]
        col_widths = [14, 18, 18, 10, 10, 14]

        for i, h in enumerate(headers):
            ws.set_column(i, i, col_widths[i])
            ws.write(2, i, h, f['header'])

        # Build monthly data
        sorted_tx = sorted(self.transactions, key=lambda x: x['date'])
        monthly = defaultdict(lambda: {"invested": 0.0, "sold": 0.0, "buys": 0, "sells": 0})

        for t in sorted_tx:
            try:
                dt = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
            except:
                dt = datetime.now()
            key = dt.strftime("%Y-%m")
            if t['type'] == "BUY":
                monthly[key]["invested"] += t['quantity'] * t['price']
                monthly[key]["buys"] += 1
            else:
                monthly[key]["sold"] += t['quantity'] * t['price']
                monthly[key]["sells"] += 1

        row = 3
        cumul = 0.0
        for month_key in sorted(monthly.keys()):
            m = monthly[month_key]
            cumul += m["invested"]
            growth = ((m["sold"] - m["invested"]) / cumul * 100) if cumul > 0 else 0
            is_alt = (row - 3) % 2 == 0

            c = f['cell_alt'] if is_alt else f['cell']
            mo = f['money_alt'] if is_alt else f['money']
            ct = f['center_alt'] if is_alt else f['center']

            ws.write(row, 0, month_key, ct)
            ws.write(row, 1, m["invested"], mo)
            ws.write(row, 2, cumul, mo)
            ws.write(row, 3, m["buys"], ct)
            ws.write(row, 4, m["sells"], ct)
            ws.write(row, 5, growth / 100, f['pct_profit'] if growth >= 0 else f['pct_loss'])
            row += 1

        if row == 3:
            ws.merge_range('A4:F4', 'No monthly data available yet.', f['subtitle'])
