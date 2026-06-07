"""
pyfiglet Demo - Large text display examples for small TFT screens
"""

try:
    from pyfiglet import figlet_format
except ImportError:
    print("pyfiglet not installed. Run: pip install pyfiglet")
    exit(1)


def demo_basic():
    """Basic large text examples"""
    print("\n=== BASIC DEMO ===\n")
    print(figlet_format('HDR'))
    print(figlet_format('SDR'))
    print(figlet_format('OK'))


def demo_different_fonts():
    """Show different font styles"""
    print("\n=== DIFFERENT FONTS ===\n")
    
    fonts = ['banner', 'big', 'block', 'bubble', 'digital', 'mini', 'small']
    
    for font in fonts:
        print(f"\nFont: {font}")
        try:
            print(figlet_format('HDR', font=font))
        except:
            print(f"Font '{font}' not available")


def demo_small_screen():
    """Compact formats suitable for 3.5 inch TFT screen"""
    print("\n=== SMALL SCREEN OPTIMIZED ===\n")
    
    # These fonts work well on small screens
    print("Font: banner")
    print(figlet_format('HDR', font='banner'))
    
    print("\nFont: digital")
    print(figlet_format('SDR', font='digital'))
    
    print("\nFont: mini")
    print(figlet_format('MODE', font='mini'))


def demo_status_messages():
    """Simulate status display like in runner.py"""
    print("\n=== STATUS MESSAGES ===\n")
    
    # HDR mode change
    print(figlet_format('HDR', font='banner'))
    print("→ USER3\n")
    
    # SDR mode change
    print(figlet_format('SDR', font='banner'))
    print("→ USER1\n")
    
    # OK status
    print(figlet_format('OK', font='digital'))


if __name__ == "__main__":
    print("PyFiglet Demo for Raspberry Pi 3 with 3.5\" TFT Screen")
    print("=" * 50)
    
    demo_basic()
    demo_small_screen()
    demo_status_messages()
    
    # Uncomment to see all available fonts:
    # demo_different_fonts()
    
    print("\n" + "=" * 50)
    print("Demo complete!")
