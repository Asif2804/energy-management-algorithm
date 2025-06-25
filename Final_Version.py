import time
import requests
import pandas as pd
from gpiozero import Button
from gpiozero import LED
from gpiozero import Motor



#API setup
url = ('https://api.octopus.energy/v1/products/AGILE-18-02-21/' +
         'electricity-tariffs/E-1R-AGILE-18-02-21-C/standard-unit-rates/' +
         '?period_from=2024-03-11T00:00Z&period_to=2024-03-12T00:00Z')
r = requests.get(url)
output_dict = r.json()
valid_from = [x['valid_from'] for x in output_dict['results']]
value_exc_vat = [x['value_exc_vat'] for x in output_dict['results']]

# Energy Prices
energy_prices = pd.Series(value_exc_vat, index=valid_from)

Washing_Machine = Motor(24, 23)

# Battery
battery_level = 15
charging = False

# LED objects
charging_led = LED(22)  # blue LED
battery_charged_led = LED(27)  # green LED
battery_low_led = LED(17)  # red LED


# Thresholds
upper_threshold = 20.00
lower_threshold = 14.00


# Function to turn off all LEDs
#def turn_off_leds():
   # charging_led.off()
   # battery_charged_led.off()
   # battery_low_led.off()



plugged_led = LED(16)
Car_button = 26
Plugged = False

def toggle_plugged():
    global Plugged
    Plugged = not Plugged
    if Plugged:
        plugged_led.blink(1)
    else:
        print("Car is unplugged.")
        plugged_led.off()

# Assign the toggle_plugged function to the button 
CButton = Button(Car_button)
CButton.when_pressed = toggle_plugged

# Function to charge the car based on the Plugged status
def charge_car():
    global Plugged
    if Plugged:
        print("Charging the EV car.")
        # Code to simulate car charging
    else:
        print("Please plug in your car to charge.")


# Washing machine
Ready_led = LED(6)
WashingM_button = 5
Ready = True

def toggle_Ready():
    global Ready
    Ready = not Ready
    if Ready:
        Ready_led.blink(1)
       
    else:
        print("Washing Machine is empty.")
        Ready_led.off()

# Assign the toggle_plugged function to the button 
washing_button = Button(WashingM_button)
washing_button.when_pressed = toggle_Ready

def turn_on_washing_machine():
    global Ready
    if Ready:
        print("Turning on the washing machine.")
        Washing_Machine.forward(1)
        time.sleep(7)
        Washing_Machine.forward(0)
    else:
        print("Condition is not met. Washing machine remains off.")




# Function to use energy off the grid 
def use_energy_off_grid(): 
    global battery_level
    battery_level -= 15  # Charging decrease battery level by 15%
    if battery_level < 0:  # Check if battery level exceeds 100%
        battery_level = 0  # Limit battery level to 100%
    print("Battery used =", battery_level,"%")


    # Function to use energy off the grid 
def use_energy_from_grid(): 
    print("Using energy from the grid") 


# Function to charge the battery 
def charge_battery():
    global charging, battery_level
    if battery_level < 85:  # Ensure battery isn't already full
        print("Low battery")
        battery_low_led.on()
        time.sleep(3)
        battery_low_led.off()
        charging = True
        print("Charging the battery")
        
        # Simulate charging process
        charging_led.blink(1)
        time.sleep(4)
        charging_led.off()
        
        battery_level += 15  # Charging increases battery level by 15%
        if battery_level > 100:  # Check if battery level exceeds 100%
            battery_level = 100  # Limit battery level to 100%
        print("Battery charged =", battery_level,"%")
        battery_charged_led.on()
        time.sleep(1)
        battery_charged_led.off()
        charging = False
    else:
        print("Battery is full.")
        battery_charged_led.blink(0.5)
        time.sleep(4)
        battery_charged_led.off()

# Find the 2 slots with highest energy prices 
highest_prices_index = sorted(range(len(energy_prices)), key=energy_prices.__getitem__, reverse=True)[:2]

# Find the 2 indices of the two second highest prices
second_highest_prices_index = sorted(range(len(energy_prices)), key=energy_prices.__getitem__, reverse=True)[2:4]

# Find the 3 indices of the two lowest prices
lowest_prices_index = sorted(range(len(energy_prices)), key=energy_prices.__getitem__)[:3]


# Adjust the slice indices to exclude highest and second-highest index numbers
start_index = second_highest_prices_index[1] + 1  # Start from the index after the second highest
end_index = max(highest_prices_index) - 1  # End before the highest index
prices_in_between = energy_prices[start_index:end_index]


for hour, price in enumerate(energy_prices, start=0):
    # Convert hour to 24-hour format for display
    hour_24 = (hour - 1) // 2 + 1
    # Convert hour to 12-hour format for display
    hour_12 = hour_24 if hour_24 <= 12 else hour_24 - 12
    # AM/PM
    am_pm = 'AM' if hour_24 < 12 else 'PM'

    print(f"\n Time {hour_24}:{'30' if hour % 2 == 0 else '00'} {am_pm}: Energy price = {price}")
    

 # Make decisions based on energy price and battery    
    if hour in highest_prices_index and battery_level >= 40: 
        print("Battery =", battery_level,"%")
        use_energy_off_grid()
        print("Use energy off the grid during the highest prices and sufficient battery")  
        
        
    elif hour in second_highest_prices_index and battery_level >= 60:
        # Check if the prices in between are lower or equal to lower thrashhold
        if all(price <= lower_threshold for price in prices_in_between):
            time_to_charge = max(highest_prices_index) - second_highest_prices_index[0]
            if time_to_charge < 0:
                time_to_charge = 0  # Limit time_to_charge to 0 if it's negative

            print("Battery =", battery_level,"%")

            if battery_level + time_to_charge * 15 >= 85:
                print("Using battery for the second highest price period")
                use_energy_off_grid()
            else:
                use_energy_from_grid()
        else:
            use_energy_from_grid()
        

    elif hour in lowest_prices_index:
        # Call the function to charge EV
        charge_car()

        # Call the function to turn on the washing machine
        turn_on_washing_machine()
        use_energy_from_grid()
        charge_battery()
  

    elif hour > second_highest_prices_index[1] and hour < max(highest_prices_index):
        print("Battery =", battery_level,"%")
        print("Charging the battery between the second highest and highest energy price periods")
        charge_battery()

    # Check if it's a suitable time to charge the battery based on low energy price and low battery level.
    elif price <= lower_threshold and battery_level < 85:
        if second_highest_prices_index[0] < min(highest_prices_index):
            #calc time to charge
            time_to_charge = max(highest_prices_index) - second_highest_prices_index[0]
            if battery_level + time_to_charge * 15 >= 85:
                if any(price <= lower_threshold for price in energy_prices[second_highest_prices_index[0]:max(highest_prices_index)]):
                    print("Using enery from the grid and charging the battery at low cost")
                    charge_battery()
                else:
                    use_energy_from_grid()
                    print('c')
            else:
                use_energy_from_grid()
                print('b')
        else:
            use_energy_from_grid()
            charge_battery()
            print('a')

    elif price >= upper_threshold and battery_level <= 20:
        # Use energy from the grid
        print("Price is high, but have to use energy from the grid due to insufficent battery")
        use_energy_from_grid()
        # charge_battery() when the price is low again #
    

    elif hour > max(highest_prices_index) and battery_level >= 20:
        print('Using after the highest period')
        # Use battery if enough charge left after highest price period
        use_energy_off_grid()
    
    else:
       print('Default, ')
       use_energy_from_grid()

    time.sleep(10)