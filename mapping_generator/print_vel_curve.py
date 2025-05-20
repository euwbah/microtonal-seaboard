import math

# Low sens curve: https://www.desmos.com/calculator/scfo7kcuai
functions = [
    lambda x: math.pow(x, 0.7) + 0.1,
    lambda x: 0.5 + 0.69 * (x - 0.27)
]
"""
Piecewise functions for parameter 0 <= x <= 1 corresponding to input velocity 0-127. The output
should be between 0 to 1.
"""
domains = [
    0.27,
]
"""
Where to separate piecewise functions. Strictly ascending. Each number is the inclusive lower bound
for the next function and the exclusive upper bound for the current function.
"""

# Very low sens curve: https://www.desmos.com/calculator/mrcpttdopu
functions = [
    lambda x: math.pow(x, 0.66) + 0.1,
    lambda x: 0.732878 + (1 - 0.732878) / (1 - 0.5) * (x - 0.5)
]
domains = [
    0.5
]

# Med low sens curve: https://www.desmos.com/calculator/o3wzney1qh
# functions = [
#     lambda x: math.pow(x, 0.75) + 0.02,
#     lambda x: 0.6146 + (1 - 0.6146) / (1 - 0.5) * (x - 0.5)
# ]

# domains = [
#     0.5,
# ]

# Default curve
# functions = [
#     lambda x: x
# ]
# domains = []

# High sens curve: https://www.desmos.com/calculator/bverl3ybw2
# functions = [
#     lambda x: 0,
#     lambda x: math.pow(x, 1.5) * 126/127 + 1/127
# ]
# domains = [1/127]

vels = []
for i in range(128):
    x = i / 127
    if len(domains) == 0:
        y = functions[0](x)
    else:
        for j in range(len(domains)):
            if x < domains[j]:
                y = functions[j](x)
                break
        else:
            y = functions[-1](x)

    vel = round(y * 127)
    if vel < 0:
        vel = 0
    if vel > 127:
        vel = 127

    vels.append(vel)

print(' '.join([str(v) for v in vels]))
