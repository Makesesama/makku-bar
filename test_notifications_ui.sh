#!/usr/bin/env bash

echo "Testing notification system..."

# Test basic notification
echo "1. Basic notification"
notify-send "Hello!" "Your notification system is working!"
sleep 2

# Test with icon
echo "2. Notification with icon"
notify-send -i dialog-information "Info" "This has an information icon"
sleep 2

# Test urgency levels
echo "3. Testing urgency levels"
notify-send -u low "Low Priority" "This is low priority"
sleep 1
notify-send -u normal "Normal Priority" "This is normal priority"
sleep 1
notify-send -u critical "Critical Priority" "This is critical priority"
sleep 2

# Test long message
echo "4. Long message test"
notify-send "Long Message Test" "This is a very long notification message that should test how well the notification bubble handles longer text content and whether it displays properly in your status bar notification system."
sleep 3

# Test rapid notifications
echo "5. Rapid notifications test"
for i in {1..5}; do
    notify-send "Message $i" "Testing notification queue handling"
    sleep 0.5
done

echo "Notification tests complete! Check your status bar."
