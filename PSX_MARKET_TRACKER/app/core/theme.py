def get_theme_stylesheet(theme_name):
    """Returns the CSS stylesheet string for the requested theme with modern touch."""
    
    # --- COMMON SLICK SCROLLBAR STYLE ---
    scrollbar_style = """
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(16, 185, 129, 0.2);
            min-height: 20px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(16, 185, 129, 0.5);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """

    # If the user selected LIGHT theme (Inspired by professional dashboards)
    if theme_name.lower() == "light":
        
        bg_main = "#f8fafc"      # Clean slate white
        bg_sidebar = "#ffffff"   # Pure white
        bg_card = "#ffffff"      # Elevated white cards
        text_main = "#0f172a"    # Deep dark slate (CRITICAL FOR READABILITY)
        text_dim = "#64748b"     # Muted slate gray
        accent = "#10b981"       # Emerald
        border = "#e2e8f0"       # Soft border
        
        return f"""
            /* Global */
            QMainWindow {{ background-color: {bg_main}; }}
            QWidget {{ color: {text_main}; font-family: 'Inter', 'Segoe UI', sans-serif; }}
            
            /* Frames & Cards with soft shadows */
            QFrame {{ 
                background-color: {bg_card}; 
                border: 1px solid {border};
                border-radius: 14px; 
            }}
            
            #sidebar {{ 
                background-color: {bg_sidebar}; 
                border: none; 
                border-right: 1px solid {border}; 
                border-radius: 0px;
            }}
            
            #header {{ 
                background-color: {bg_sidebar}; 
                border: none; 
                border-bottom: 2px solid {border};
                border-radius: 0px;
            }}
            
            /* Typography Adaptive Classes */
            .title-text {{ color: {text_main}; }}
            .desc-text {{ color: {text_dim}; }}
            
            /* Table Modernization */
            QTableWidget {{ 
                background-color: {bg_card}; 
                gridline-color: {border}; 
                border: none;
                color: {text_main};
                outline: none;
            }}
            QHeaderView::section {{ 
                background-color: #f1f5f9; 
                color: {text_dim}; 
                border: none;
                border-bottom: 1px solid {border};
                padding: 12px;
                font-weight: 600;
            }}
            QTableWidget::item {{ 
                color: {text_main}; 
                border-bottom: 1px solid #f1f5f9; 
                outline: none;
            }}
            QTableWidget::item:selected {{ 
                background-color: #f0fdf4; 
                color: {accent}; 
                outline: none;
                border: none;
            }}
            QTableWidget::item:focus {{ 
                outline: none;
                border: none;
            }}

            /* Buttons */
            QPushButton {{ 
                background-color: {accent}; 
                color: white; 
                border-radius: 10px; 
                padding: 10px; 
                font-weight: 600;
            }}
            
            {scrollbar_style}
        """
        
    # Default: PREMIUM GLASS DARK THEME
    else:
        
        bg_main = "#09090b"      # OLED black
        bg_card = "rgba(255, 255, 255, 0.04)"
        text_main = "#f8fafc"    # High contrast white
        text_dim = "#94a3b8"     # Slate blue/gray
        accent = "#10b981"       # PSX Green
        border = "rgba(255, 255, 255, 0.08)"
        
        return f"""
            /* Global */
            QMainWindow {{ background-color: {bg_main}; font-family: 'Inter', 'Segoe UI', sans-serif; }}
            QWidget {{ color: {text_main}; }}
            
            /* Glassmorphic Elements */
            QFrame {{ 
                background-color: {bg_card}; 
                border: none;
                border-radius: 18px;
            }}
            
            #sidebar {{ background-color: {bg_main}; border: none; border-right: none; border-radius: 0px; }}
            #header {{ background-color: {bg_main}; border: none; border-bottom: none; border-radius: 0px; }}
            
            /* Typography Adaptive Classes */
            .title-text {{ color: {text_main}; }}
            .desc-text {{ color: {text_dim}; }}

            /* Inputs */
            QLineEdit {{
                background-color: rgba(15, 23, 42, 0.5);
                border: none;
                border-radius: 12px;
                padding: 12px;
                color: white;
            }}

            /* Table Modernization (Dark) */
            QTableWidget {{
                outline: none;
                gridline-color: {border};
                border: none;
            }}
            QTableWidget::item {{
                outline: none;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(16, 185, 129, 0.1);
                color: {accent};
                outline: none;
                border: none;
            }}
            QTableWidget::item:focus {{
                outline: none;
                border: none;
            }}

            /* Buttons */
            QPushButton {{
                background-color: {accent};
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-weight: 600;
                border: none;
            }}
            
            {scrollbar_style}
        """
