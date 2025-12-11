"""
test_router.py - Unit tests for the Router class

Tests navigation logic without GUI dependencies.
"""

from routes import Router, ViewType


def test_router_initialization():
    """Test router initializes with default values."""
    router = Router()
    assert router.current_view == ViewType.RESULTS
    assert router.contingency_group_visible == True
    assert router.is_in_results_mode() == True
    assert router.is_in_editor_mode() == False
    print("✓ Router initialization test passed")


def test_navigate_to_results():
    """Test navigating to results view."""
    router = Router()
    router.navigate_to("new_network")
    assert router.current_view == ViewType.NEW_NETWORK
    
    result = router.navigate_to("results")
    assert result == True
    assert router.current_view == ViewType.RESULTS
    assert router.get_view_index() == 0
    assert router.contingency_group_visible == True
    print("✓ Navigate to results test passed")


def test_navigate_to_new_network():
    """Test navigating to new network editor."""
    router = Router()
    result = router.navigate_to("new_network")
    assert result == True
    assert router.current_view == ViewType.NEW_NETWORK
    assert router.get_view_index() == 1
    assert router.contingency_group_visible == False
    assert router.is_in_editor_mode() == True
    print("✓ Navigate to new network test passed")


def test_invalid_navigation():
    """Test invalid view name."""
    router = Router()
    result = router.navigate_to("invalid_view")
    assert result == False
    assert router.current_view == ViewType.RESULTS  # Should remain unchanged
    print("✓ Invalid navigation test passed")


def test_theme_toggle():
    """Test theme toggling."""
    router = Router()
    
    # Register a callback to track theme changes
    theme_changes = []
    router.register_theme_callback("test", lambda t: theme_changes.append(t))
    
    new_theme = router.toggle_theme("dark")
    assert new_theme == "light"
    assert "light" in theme_changes
    
    new_theme = router.toggle_theme("light")
    assert new_theme == "dark"
    assert "dark" in theme_changes
    print("✓ Theme toggle test passed")


def test_view_callbacks():
    """Test view navigation callbacks."""
    router = Router()
    
    callbacks_executed = []
    router.register_view_callback("results", lambda: callbacks_executed.append("results"))
    router.register_view_callback("new_network", lambda: callbacks_executed.append("new_network"))
    
    router.navigate_to("new_network")
    assert "new_network" in callbacks_executed
    
    router.navigate_to("results")
    assert "results" in callbacks_executed
    print("✓ View callbacks test passed")


def test_network_callbacks():
    """Test network event callbacks."""
    router = Router()
    
    network_events = []
    router.register_network_callback("test", lambda name, obj: network_events.append(name))
    
    router.on_network_loaded("case14", None)
    assert "case14" in network_events
    print("✓ Network callbacks test passed")


def test_state_queries():
    """Test state query methods."""
    router = Router()
    
    assert router.is_in_results_mode() == True
    assert router.is_in_editor_mode() == False
    assert router.get_current_view_name() == "results"
    
    router.navigate_to("new_network")
    assert router.is_in_results_mode() == False
    assert router.is_in_editor_mode() == True
    assert router.get_current_view_name() == "new_network"
    print("✓ State queries test passed")


def test_contingency_visibility():
    """Test contingency group visibility management."""
    router = Router()
    
    assert router.should_show_contingencies() == True
    
    router.navigate_to("new_network")
    assert router.should_show_contingencies() == False
    
    router.navigate_to("results")
    assert router.should_show_contingencies() == True
    print("✓ Contingency visibility test passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Running Router Unit Tests")
    print("="*60 + "\n")
    
    test_router_initialization()
    test_navigate_to_results()
    test_navigate_to_new_network()
    test_invalid_navigation()
    test_theme_toggle()
    test_view_callbacks()
    test_network_callbacks()
    test_state_queries()
    test_contingency_visibility()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")
