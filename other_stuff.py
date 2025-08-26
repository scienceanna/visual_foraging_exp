import math
import numpy as np

def gen_1overf_noise(beta=1.0, n=256):
    """Generate 1/f noise."""
    # Create frequency grid
    freqs = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(freqs, freqs)
    f = np.sqrt(fx**2 + fy**2)
    f[0, 0] = 1  # Avoid division by zero
    
    # Generate 1/f^beta spectrum
    spectrum = f**(-beta/2) * np.exp(1j * 2*np.pi * np.random.random((n, n)))
    spectrum[0, 0] = 0  # Zero DC component
    
    # Generate noise
    noise = np.fft.ifft2(spectrum).real
    # Scale to [0, 1]
    noise = noise - noise.min()
    noise = noise / noise.max()

    return noise

def get_grid(rows, cols, theta, es):

    # some parameters
    jiggle_param = es.jiggle # how much random jitter should we add

    # if we are using a circular aperture, we will need to make the underlying grid larger

    xmin = es.width_border
    xmax = es.scrn_width - es.width_border
    ymin = es.height_border
    ymax = es.scrn_height - es.height_border

    r = math.sqrt((xmax - xmin) * (ymax - ymin)) / math.pi

    # create one-dimensional arrays for x and y
    # generate twice as many as required so 
    # we will fill the search space with items
    # even after rotation
    x = np.linspace(-1, 2, 3*cols) 
    y = np.linspace(-1, 2, 3*rows)

    # create the mesh based on these arrays
    x, y = np.meshgrid(x, y)

    # convert into 1D vector
    x = x.reshape((np.prod(x.shape),))
    y = y.reshape((np.prod(y.shape),))

    # scale to correct size
    x = (es.scrn_width  - 2*es.width_border)  * x + es.width_border
    y = (es.scrn_height - 2*es.height_border) * y + es.height_border
  
    idx = (x > es.width_border) * (x < es.scrn_width - es.width_border) * (y > es.height_border) * (y < es.scrn_height - es.height_border) 
    #x = x[idx]
    #y = y[idx]

    # translate so that (0, 0) is the centre of the screen
    x = x - es.scrn_width/2
    y = y - es.scrn_height/2

    # rotate lattice
    xr = np.cos(theta) * x - np.sin(theta) * y
    yr = np.sin(theta) * x + np.cos(theta) * y

    x = xr
    y = yr 
    
    # take only points that fall inside a circle
    idx = ((x)**2 + (y)**2) < r**2
    x = x[idx]
    y = y[idx]

    # apply random jiggle and round
    x = np.around(x + jiggle_param * np.random.randn(len(x)))
    y = np.around(y + jiggle_param * np.random.randn(len(y)))

    item_id = range(1, rows*cols+1)

    return(list(zip(x, y, item_id)))

def uniform_random_placement(n_items, es):

    xmin = es.width_border
    xmax = es.scrn_width - es.width_border
    ymin = es.height_border
    ymax = es.scrn_height - es.height_border

    x = np.around(np.random.uniform(xmin, xmax, n_items)) - es.scrn_width/2
    y = np.around(np.random.uniform(ymin, ymax, n_items)) - es.scrn_height/2
    
    item_id = range(1, n_items+1)

    return(list(zip(x, y, item_id)))

def closest_point_on_line(ax, ay, bx, by, px, py):
    """
    Calculate the closest point on a line defined by points A(ax, ay) and B(bx, by)
    to a point P(px, py).

    :param ax: x-coordinate of point A
    :param ay: y-coordinate of point A
    :param bx: x-coordinate of point B
    :param by: y-coordinate of point B
    :param px: x-coordinate of point P
    :param py: y-coordinate of point P
    :return: (qx, qy) coordinates of the closest point Q on the line to point P
    """

    # Vector AB
    abx, aby = bx - ax, by - ay

    # Vector AP
    apx, apy = px - ax, py - ay

    # Calculating the dot products
    ab_dot_ab = abx * abx + aby * aby
    ap_dot_ab = apx * abx + apy * aby

    # Calculating the ratio
    t = ap_dot_ab / ab_dot_ab

    # Finding the closest point Q
    qx = ax + t * abx
    qy = ay + t * aby

    return qx, qy
