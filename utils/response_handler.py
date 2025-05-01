def make_empathic(response):
    """More natural empathy rotation"""
    empathic_phrases = [
        "I hear how difficult this feels",
        "That sounds really challenging",
        "I appreciate you sharing this with me",
        "I can sense this is weighing on you",
        "You're being so brave by working through this"
    ]
    
    from random import choice
    return f"{choice(empathic_phrases)}. {response}"

#makes the function natural 
__all__ = ['make_empathic']