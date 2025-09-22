from datetime import datetime, timedelta

def format_duration(seconds):
    """Format seconds as a human-readable duration"""
    if not seconds:
        return "0 seconds"
    
    try:
        seconds = float(seconds)
        if seconds < 60:
            return f"{int(seconds)} seconds"
        
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)} minutes"
        
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)} hours, {int(minutes % 60)} minutes"
        
        days = hours / 24
        return f"{int(days)} days, {int(hours % 24)} hours"
    except (ValueError, TypeError):
        return "Invalid duration"

def format_volume(gallons):
    """Format gallons as a human-readable volume"""
    if not gallons:
        return "0 gallons"
    
    try:
        gallons = float(gallons)
        if gallons < 10:
            return f"{gallons:.2f} gallons"
        elif gallons < 1000:
            return f"{int(gallons)} gallons"
        elif gallons < 1000000:
            return f"{gallons/1000:.1f} thousand gallons"
        else:
            return f"{gallons/1000000:.2f} million gallons"
    except (ValueError, TypeError):
        return "Invalid volume"

def format_timestamp(iso_timestamp):
    """Format ISO timestamp as a human-readable date/time"""
    if not iso_timestamp:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        
        # If today, show time only
        if dt.date() == now.date():
            return dt.strftime("Today at %I:%M %p")
        
        # If yesterday, show "Yesterday"
        yesterday = now.date() - timedelta(days=1)
        if dt.date() == yesterday:
            return dt.strftime("Yesterday at %I:%M %p")
        
        # If within last 7 days, show day name
        if (now.date() - dt.date()).days < 7:
            return dt.strftime("%A at %I:%M %p")
        
        # Otherwise show full date
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return "Invalid timestamp"

def get_state_color(state):
    """Get Bootstrap color class for tank state"""
    state_colors = {
        'HIGH': 'success',
        'MID': 'info',
        'LOW': 'warning',
        'EMPTY': 'danger',
        'ERROR': 'secondary',
        'unknown': 'secondary'
    }
    return state_colors.get(state, 'secondary')