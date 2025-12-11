"""
routes.py - Navigation Router for Power System Dashboard

Centralizes all navigation logic and view state management.
"""

from enum import Enum
from typing import Callable, Optional, Dict, Any


class ViewType(Enum):
    """Enum for available application views."""
    RESULTS = "results"
    NEW_NETWORK = "new_network"


class Router:
    """
    Router class to manage application navigation and state transitions.
    Decouples navigation logic from UI components.
    """
    
    def __init__(self):
        self.current_view = ViewType.RESULTS
        self._view_callbacks: Dict[str, Callable] = {}
        self._theme_callbacks: Dict[str, Callable] = {}
        self._network_callbacks: Dict[str, Callable] = {}
        self.contingency_group_visible = True
    
    # ============ View Navigation ============
    
    def register_view_callback(self, name: str, callback: Callable):
        """Register a callback to be invoked when navigating to a view."""
        self._view_callbacks[name] = callback
    
    def navigate_to(self, view_name: str) -> bool:
        """
        Navigate to a specific view.
        
        Args:
            view_name: Either 'results' or 'new_network'
            
        Returns:
            True if navigation was successful, False otherwise
        """
        if view_name == "new_network":
            self.current_view = ViewType.NEW_NETWORK
            self.contingency_group_visible = False
        elif view_name == "results":
            self.current_view = ViewType.RESULTS
            self.contingency_group_visible = True
        else:
            return False
        
        # Execute registered callbacks
        if view_name in self._view_callbacks:
            self._view_callbacks[view_name]()
        
        return True
    
    def get_view_index(self) -> int:
        """Get the stack index for the current view."""
        return 1 if self.current_view == ViewType.NEW_NETWORK else 0
    
    # ============ Theme Management ============
    
    def register_theme_callback(self, name: str, callback: Callable):
        """Register a callback to be invoked on theme change."""
        self._theme_callbacks[name] = callback
    
    def toggle_theme(self, current_theme: str) -> str:
        """
        Toggle between light and dark themes.
        
        Args:
            current_theme: Current theme ('dark' or 'light')
            
        Returns:
            New theme name
        """
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        
        # Execute all registered callbacks
        for callback in self._theme_callbacks.values():
            try:
                callback(new_theme)
            except Exception as e:
                print(f"Error in theme callback: {e}")
        
        return new_theme
    
    # ============ Network Management ============
    
    def register_network_callback(self, name: str, callback: Callable):
        """Register a callback to be invoked on network changes."""
        self._network_callbacks[name] = callback
    
    def on_network_loaded(self, network_name: str, net_object: Any = None):
        """
        Trigger callbacks when a network is loaded.
        
        Args:
            network_name: Name of the loaded network
            net_object: The network object (optional)
        """
        for callback in self._network_callbacks.values():
            try:
                callback(network_name, net_object)
            except Exception as e:
                print(f"Error in network callback: {e}")
    
    # ============ Contingency Visibility ============
    
    def should_show_contingencies(self) -> bool:
        """Return whether contingency group should be visible."""
        return self.contingency_group_visible
    
    # ============ State Queries ============
    
    def is_in_editor_mode(self) -> bool:
        """Check if currently in new network editor mode."""
        return self.current_view == ViewType.NEW_NETWORK
    
    def is_in_results_mode(self) -> bool:
        """Check if currently in results view mode."""
        return self.current_view == ViewType.RESULTS
    
    def get_current_view_name(self) -> str:
        """Get the name of the current view."""
        return self.current_view.value
