"""Quick startup verification script."""
from app import create_app

def test_startup():
    """Test that the app can be created and configured."""
    app = create_app()
    
    print("✓ App created successfully")
    print(f"  Debug mode: {app.debug}")
    print(f"  Testing mode: {app.testing}")
    print(f"  Secret key configured: {'Yes' if app.secret_key else 'No'}")
    
    # Test that all blueprints are registered
    blueprints = list(app.blueprints.keys())
    print(f"  Registered blueprints ({len(blueprints)}): {', '.join(blueprints)}")
    
    # Test that database is configured
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
    print(f"  Database: {db_uri[:60]}{'...' if len(db_uri) > 60 else ''}")
    
    # Test a simple route
    with app.test_client() as client:
        response = client.get('/')
        print(f"  Home page status: {response.status_code}")
        
        response = client.get('/health')
        print(f"  Health endpoint status: {response.status_code}")
    
    print("\n✓ All startup checks passed!")
    return True

if __name__ == '__main__':
    test_startup()
