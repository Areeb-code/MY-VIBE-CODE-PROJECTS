import os
import sys
import io

# Force UTF-8 encoding for Windows consoles to prevent encoding errors
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path so we can import app
sys.path.insert(0, os.path.abspath('.'))

from app.core.db import init_db
from app.core.auth import (
    authenticate, 
    create_owner, 
    register_broker, 
    create_client,
    ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT
)
from app.core.managers import PortfolioManager

def test_backend_flow():
    print("Testing Backend Flow...")
    
    # Use a temporary test database
    os.environ["DB_PATH"] = "test_data.db"
    
    # 1. Init DB
    if os.path.exists("test_data.db"):
        os.remove("test_data.db")
    init_db()
    print("DB Init successful")
    
    # 2. Setup Owner
    owner_session = create_owner("Owner", "owner@psx.com", "ownerpass")
    assert owner_session, "Failed to setup owner"
    print("Owner setup successful")
    
    # 3. Authenticate Owner
    owner_session = authenticate("owner@psx.com", "ownerpass")
    assert owner_session and owner_session.role == ROLE_OWNER, "Failed to auth owner"
    print("Owner auth successful")
    
    # 4. Register Broker
    res = register_broker("Broker Alpha", "broker1@psx.com", "brokerpass")
    assert res.get('success'), f"Failed to register broker: {res.get('error')}"
    
    # 5. Authenticate Broker
    broker_session = authenticate("broker1@psx.com", "brokerpass")
    assert broker_session and broker_session.role == ROLE_BROKER, "Failed to auth broker"
    print("Broker auth successful")
    
    # 6. Create Client (by Broker)
    res = create_client(broker_session, "Client X", "clientx@psx.com", "clientpass")
    assert res.get('success'), f"Failed to create client: {res.get('error')}"
    print("Client creation successful")
    
    # 7. Authenticate Client
    client_session = authenticate("clientx@psx.com", "clientpass")
    assert client_session and client_session.role == ROLE_CLIENT, "Failed to auth client"
    print("Client auth successful")
    
    # 8. Test Data Isolation
    broker_manager = PortfolioManager(session=broker_session)
    client_manager = PortfolioManager(session=client_session)
    
    # Broker adds a stock for the client
    # The signature in PortfolioManager is add_or_update_stock(symbol, qty, buy_price, high_limit, low_limit, client_id)
    broker_manager.add_or_update_stock("SYS", 100, 50.0, 100.0, 40.0, client_id=client_session.user_id)
    
    # Client should see it
    client_portfolio = client_manager.get_aggregated_portfolio()
    assert "SYS" in client_portfolio, "Client cannot see their own portfolio added by broker"
    print("Client can see data added by broker for them")
    
    # Create another client and broker to verify strict isolation
    res = register_broker("Broker Beta", "broker2@psx.com", "brokerpass2")
    broker2_session = authenticate("broker2@psx.com", "brokerpass2")
    
    res = create_client(broker2_session, "Client Y", "clienty@psx.com", "clientpass2")
    client2_session = authenticate("clienty@psx.com", "clientpass2")
    
    client2_manager = PortfolioManager(session=client2_session)
    client2_portfolio = client2_manager.get_aggregated_portfolio()
    assert "SYS" not in client2_portfolio, "Client Y sees Client X data!"
    print("Client isolation confirmed")
    
    broker2_manager = PortfolioManager(session=broker2_session)
    broker2_portfolio = broker2_manager.get_aggregated_portfolio()
    assert "SYS" not in broker2_portfolio, "Broker Beta sees Broker Alpha's client data!"
    print("Broker isolation confirmed")
    
    # Owner should see everything
    owner_manager = PortfolioManager(session=owner_session)
    owner_agg = owner_manager.get_aggregated_portfolio()
    assert "SYS" in owner_agg, "Owner cannot see system data"
    print("Owner visibility confirmed")
    
    print("All backend tests passed!")

if __name__ == "__main__":
    test_backend_flow()
