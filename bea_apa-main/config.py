''' Configuration file for Bea Apa - Hydration Reminder Color theme definitions and sound options.  Theme color definitions: - border: outlines for UI elements - primary: main accent color, used for primary buttons and UI highlights - secondary: used for secondary interactions and hover states - background: main application background - surface: card/dialog/widget backgrounds (lighter than background) - text: primary text color - text_secondary: secondary/muted text - accent: attention-grabbing elements and critical actions - accent_dark: darker version of accent color for hover states - highlight: subtle highlighting, low emphasis elements - overlay: hover states, subtle overlays - shadow: shadow color for 3D effects - warning: warning messages and alerts - info: informational elements - success: success messages and confirmations '''

MODERN_COLORS = {
    "dark": {
        "border": "#3A3A3C",
        "primary": "#7F5AF0",
        "secondary": "#6246EA",
        "background": "#16161A",
        "surface": "#242629",
        "text": "#FFFFFE",
        "text_secondary": "#94A1B2",
        "accent": "#EF4565",
        "accent_dark": "#CC2A45", # Added darker accent
        "highlight": "#72757E",
        "overlay": "#2E2E34",
        "shadow": "#000000",
        "warning": "#FF9500",
        "info": "#64D2FF",
        "success": "#2CB67D"
    },
    "light": {
        "border": "#DEDEDE",
        "primary": "#6246EA",
        "secondary": "#4324D7",
        "background": "#FFFFFE",
        "surface": "#F2F4F6",
        "text": "#2B2C34",
        "text_secondary": "#5F6C7B",
        "accent": "#E45858",
        "accent_dark": "#C93535", # Added darker accent
        "highlight": "#D1D1E9",
        "overlay": "#EAEAEC",
        "shadow": "#00000020",
        "warning": "#FF9500",
        "info": "#0A84FF",
        "success": "#30D158"
    },
    "dark v2": {  # Blue shades
        "border": "#3A3A3C",
        "primary": "#1e90ff",
        "secondary": "#187DE0",
        "background": "#16161A",
        "surface": "#222228",
        "text": "#FFFFFE",
        "text_secondary": "#94A1B2",
        "accent": "#EF4565",
        "accent_dark": "#CC2A45", # Added darker accent
        "highlight": "#72757E",
        "overlay": "#2E2E34",
        "shadow": "#000000",
        "warning": "#FF9500",
        "info": "#64D2FF",
        "success": "#2CB67D"
    },
    "apple dark": {
        "border": "#3A3A3C",          # Slightly lighter border for better contrast in dark mode
        "primary": "#0A84FF",         # Apple Blue - Primary interactive color
        "secondary": "#0071E3",       # Slightly darker blue for pressed states
        "background": "#1C1C1E",      # Darker background for a deeper dark mode
        "surface": "#2C2C2E",         # Card/dialog background
        "text": "#FFFFFF",            # White text for maximum readability on dark background
        "text_secondary": "#98989E",  # Secondary text color
        "accent": "#FF453A",          # Apple Red - Accent color for delete/destructive actions
        "accent_dark": "#E02D22",     # Added darker accent
        "highlight": "#8E8E93",       # Gray highlight for completed tasks - iOS Gray 3
        "overlay": "#3A3A3C",         # Overlay for hover states
        "shadow": "#000000",          # Shadow color
        "warning": "#FF9F0A",         # Apple Orange for warnings
        "info": "#64D2FF",            # Light blue for info messages
        "success": "#30D158"          # Apple Green for success messages
    },
    # Standard macOS/iOS Dark and Light themes
    "ios_dark": {
        "is_dark": True,
        "background": "#1E1E1E",      # Dark space gray
        "surface": "#262626",         # Slightly lighter gray for cards/sidebars
        "surface_raised": "#323232",  # Slightly raised elements
        "text": "#FFFFFF",            # White text
        "text_secondary": "#BBBBBB",  # Light gray secondary text
        "border": "#383838",          # Dark border gray
        "primary": "#0A84FF",         # iOS blue
        "secondary": "#52A8FF",       # Lighter blue
        "accent": "#FF453A",          # iOS red
        "accent_dark": "#D93A30",     # Darker iOS red
        "highlight": "#8E8E93",       # iOS gray
        "overlay": "#3A3A3C",         # Dark overlay
        "shadow": "#000000",          # Black shadow
        "warning": "#FF9F0A",         # iOS orange
        "info": "#5AC8FA",            # iOS light blue
        "success": "#30D158",         # iOS green
    },
    "ios_light": {
        "is_dark": False,
        "background": "#F5F5F7",      # Light gray background
        "surface": "#FFFFFF",         # White surface
        "surface_raised": "#F0F0F0",  # Slightly raised elements
        "text": "#000000",            # Black text
        "text_secondary": "#6E6E6E",  # Dark gray secondary text
        "border": "#D1D1D6",          # Light border gray
        "primary": "#0A84FF",         # iOS blue
        "secondary": "#52A8FF",       # Lighter blue
        "accent": "#FF453A",          # iOS red
        "accent_dark": "#D93A30",     # Darker iOS red
        "highlight": "#C7C7CC",       # iOS light gray
        "overlay": "#E5E5EA",         # Light overlay
        "shadow": "#00000020",        # Transparent black shadow
        "warning": "#FF9F0A",         # iOS orange
        "info": "#0A84FF",            # iOS blue
        "success": "#30D158",         # iOS green
    },
    # Ocean theme based on iOS blue
    "ocean": {
        "is_dark": True,
        "background": "#0A2740",      # Dark blue background
        "surface": "#123859",         # Slightly lighter blue surface
        "surface_raised": "#1A4B80",  # Raised elements
        "text": "#FFFFFF",            # White text
        "text_secondary": "#B0C4DE",  # Light blue secondary text
        "border": "#1A4B80",          # Medium blue border
        "primary": "#0A84FF",         # iOS blue
        "secondary": "#52A8FF",       # Lighter blue
        "accent": "#5AC8FA",          # iOS light blue
        "accent_dark": "#4AA8D4",     # Darker light blue
        "highlight": "#407AA7",       # Mid-tone blue highlight
        "overlay": "#1F4C7A",         # Bluish overlay
        "shadow": "#051526",          # Dark blue shadow
        "warning": "#FF9F0A",         # iOS orange
        "info": "#64D2FF",            # Bright blue info
        "success": "#30D158",         # iOS green
    },
    # Forest theme based on iOS green
    "forest": {
        "is_dark": True,
        "background": "#0C291A",      # Dark green background
        "surface": "#143D24",         # Slightly lighter green surface
        "surface_raised": "#1A5F2E",  # Raised elements
        "text": "#FFFFFF",            # White text
        "text_secondary": "#B0D8C0",  # Light green secondary text
        "border": "#1A5F2E",          # Medium green border
        "primary": "#30D158",         # iOS green
        "secondary": "#69D98C",       # Lighter green
        "accent": "#FFD60A",          # Yellow accent for contrast
        "accent_dark": "#EBBA00",     # Darker yellow
        "highlight": "#3A7D4A",       # Mid-tone green highlight
        "overlay": "#205532",         # Green overlay
        "shadow": "#071510",          # Dark green shadow
        "warning": "#FF9F0A",         # iOS orange
        "info": "#5AC8FA",            # iOS light blue
        "success": "#30D158",         # iOS green
    },
    # Purple theme based on iOS purple
    "purple": {
        "is_dark": True,
        "background": "#1F0F35",      # Dark purple background
        "surface": "#2D1A4A",         # Slightly lighter purple surface
        "surface_raised": "#3D2A63",  # Raised elements
        "text": "#FFFFFF",            # White text
        "text_secondary": "#C6B1E1",  # Light purple secondary text
        "border": "#3D2A63",          # Medium purple border
        "primary": "#BF5AF2",         # iOS purple
        "secondary": "#DA8FFF",       # Lighter purple
        "accent": "#5E5CE6",          # iOS indigo for accents
        "accent_dark": "#4A48C9",     # Darker indigo
        "highlight": "#644B8F",       # Mid-tone purple highlight
        "overlay": "#422C71",         # Purple overlay
        "shadow": "#0F071A",          # Dark purple shadow
        "warning": "#FF9F0A",         # iOS orange
        "info": "#5AC8FA",            # iOS light blue
        "success": "#30D158",         # iOS green
    }
}

# Available notification sounds
SOUND_OPTIONS = {
    "Normal": "assets/sounds/normal.wav",
    "Baby": "assets/sounds/baby.wav",
    "Meow": "assets/sounds/meow.wav",
    "Ding": "assets/sounds/ding.wav"
}