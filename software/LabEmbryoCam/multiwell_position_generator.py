# For generating position lists for multi-well plates

import matplotlib.pyplot as plt

# Identify relevant well to well distances for 24, 48, 96 and 384 well plates and corresponding x_wells
well_dists = {6:19, 8:13, 12:9, 24:4.5}
yLabs = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P'] 
def gen_xy_old(xy1, xWells, yWells):
    '''
    Function for generating coordinates for a given plate size, based on the
    first coordinate.
    '''
    well_dist = well_dists[xWells]

    positions = []
    for i in range(yWells):
        for j in range(xWells):
            x = (j*well_dist) + xy1[0]
            y = (-i*well_dist) + xy1[1]
            z = 0
            labels = yLabs[i]+str(j+1)
            positions.append((x,y,z,labels))

    return positions

def gen_xy(xy1, position_list):
    x,y,z,_ = xy1

    new_positions = []
    for pos in position_list:
        X = x + pos[0]
        Y = y + pos[1]
        Z = z + pos[2]
        label = pos[3]

        new_positions.append((X, Y, Z, label))

    return new_positions


# A1 pos for diff well plates

well_24 = (-145.2, -8.65)
well_48 = (-145, -6.2)
well_384 = (-151.15, -4.9)

import pandas as pd

for pos, dims in zip((well_24, well_48, well_384), ((6, 4), (8, 6), (24, 16))):
    x,y,z,label = zip(*gen_xy_old(pos, *dims))

    df = pd.DataFrame(data=dict(x=x, y=y, z=z, label=label))
    df.to_csv(f'./position_lists/multiwell_{dims[0]*dims[1]}_{well_dists[dims[0]]}')