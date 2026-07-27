# LESSON 1
# Instructions
# When we give instructions, the order matters.
# 
# Here are some mixed-up steps for brushing your teeth:

# 1. Put the toothbrush back in the holder.
# 2. Scrub your teeth with the brush.
# 3. Wet the brush under the tap.
# 4. Put toothpaste on the brush.

# Your Task:

# Write the step numbers in the correct order. 

# in python this method is a CLASS ROUTINE just as we know in golang this works like STRUCT

class Routine:
    def fix_sequence(self):
        # Replace the numbers below with the correct order.
        return [3, 4, 2, 1]

def test_routine():
    # Do not modify this testing wrapper
    my_routine = Routine()
    return my_routine.fix_sequence()


def solution():
    return test_routine()
print(solution())



# LESSON 2
#1. Update the dictionary so that "toothpaste_grams" is set to 2

#2. Update the dictionary so that "brush_time_seconds" is set to 120

#3. Ensure you are assigning integers, not strings!


# this pattern use here is called a dictionary in python in golang i might recognize this as a MAP
def set_Brushing_State():
    config = {
        "toothpaste_grams": 2,
        "brush_time_seconds": 120
    
    }
    return config

def solution():
   return set_Brushing_State()
print(solution())