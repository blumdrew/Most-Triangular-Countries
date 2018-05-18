import shapefile
from shapely.geometry import Polygon, Point

import time
import os
import math
from random import randint

'''
KNOWN ISSUES = countries are all gross looking when they have any sort of island
need to add diferent projection still
'''
#simple pythagaros
def dist(point_one, point_two=None):
    if point_two == None:
        point_two = anchor
    try:
        x1, y1 = point_one[0], point_one[1]
        x2, y2 = point_two[0], point_two[1]
    except IndexError:
        return
    except TypeError:
        return
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist

#forumla to find area of a triangle from just three points in plane
def triangle_area(points):
    try:
        ax, ay = points[0][0], points[0][1]
        bx, by = points[1][0], points[1][1]
        cx, cy = points[2][0], points[2][1]
    except TypeError:
        return
    except IndexError:
        return

    area = math.fabs((ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)) / 2)

    return area

#functions for creating the convex hull
def polar_angle(p0, p1 = None):
    if p1 == None:
        p1 = anchor
    x_dist = p0[0] - p1[0]
    y_dist = p0[1] - p1[1]
    angle = math.atan2(y_dist, x_dist)
    return angle

#for convex hull, if determinate of three points is positive, no direction change (good)
#if negative, there is some direction change
def det(p1, p2, p3):
    determinant = (p2[0] - p1[0])*(p3[1] - p1[1]) - (p2[1] - p1[1])*(p3[0] - p1[0])

    return determinant

def sort_by_angle(points):
    if len(points) <= 1:
        return points
    #use a random pivot start
    piv_angle = polar_angle(points[randint(0, len(points) - 1)])
    smaller, equal, larger = [], [], []
    for point in points:
        point_angle = polar_angle(point)
        if point_angle < piv_angle:
            smaller.append(point)
        elif point_angle == piv_angle:
            equal.append(point)
        else:
            larger.append(point)
    return sort_by_angle(smaller) + equal + sort_by_angle(larger)
    
def convex_hull(points):
    global anchor
    #create our anchor/starting point
    sorted_by_y = sorted(points, key = lambda x: (x[1], x[0]))
    anchor = sorted_by_y[0]
    #sort by polar angle and remove anchor from list so its not added twice
    sorted_points = sort_by_angle(points)
    del sorted_points[sorted_points.index(anchor)]

    hull = [anchor, sorted_points[0]]
    #loop over rest of points, sorted by angle
    for pt in sorted_points[1:]:
        while det(hull[-2], hull[-1], pt) <= 0:
            #remove point if it rotates the wrong way
            del hull[-1]
            if len(hull) < 2:
                #something went wrong if this happens
                break
        hull.append(pt)
        
    return hull

#Want the points to create the triangle with maximum area
#See https://stackoverflow.com/questions/1621364/ 
def find_points(point_list):
    if len(point_list) < 3:
        return 'Not enough points'
    elif len(point_list) == 3:
        return point_list

    #arranged by index, not by actual points
    a, b, c = 0, 1, 2
    best_a, best_b, best_c = a, b, c
    n = len(point_list)
    count = 0
    while True: #loop for a
        bcount = 0
        while True: #loop for b
            ccount = 0
            #loop for c -> check to see if area is greater by increasing c
            while (triangle_area([point_list[a] ,point_list[b], point_list[c]]) <=
            triangle_area([point_list[a], point_list[b], point_list[(c + 1) % n]])):
                c = (c + 1) % n
                ccount += 1
                if ccount > 2*n:
                    break
                
            #test to see if changing b increases area
            if(triangle_area([point_list[a], point_list[b], point_list[c]]) <=
            triangle_area([point_list[a], point_list[(b + 1) % n], point_list[c]])):
                b = (b + 1) % n
                bcount += 1
                if bcount > 2*n:
                    break
                continue
            else:
                break
            
        #check to see if current area is greater than the best so far
        if (triangle_area([point_list[a], point_list[b], point_list[c]]) >
        triangle_area([point_list[best_a], point_list[best_b], point_list[best_c]])):
            best_a = a; best_b = b; best_c = c

        a = (a + 1) % n
        if a == b:
            b = (b + 1) % n
        if b == c:
            c = (c + 1) % n
        if a == 0:
            break

    best_three = [point_list[best_a], point_list[best_b], point_list[best_c]]
    return best_three

def get_data(country_index = 255, path='/Users/andrewlindstrom/Downloads/ne_10m_admin_0_countries'):
    os.chdir(path)
    sf = shapefile.Reader('ne_10m_admin_0_countries')
    records = sf.records()
    #loop through all countries/territories in sf
    #name should be in records[terr][8]
    all_data = [[terr[8]] for terr in records]

    #need to add on the country data->will have to transform to azimuthal
    #projection before final, but for now just use raw

    """
INSERT FUNCTION TO TRANSFORM POINTS FROM MERCATOR PROJ TO BETTER ONE
    """

    #if no index is chosen, or a value > 254, just return all
    if country_index > 254:
        for index in range(len(records)):
            points = sf.shapes()[index].points
            center = Polygon(points).centroid.coords[0]
            poly_area = Polygon(points).area
            #only points in convex shell are valid for triangle making
            convex_shell = convex_hull(points)
            triangle = find_points(convex_shell)
            score = round(triangle_area(triangle)/poly_area, 3)
            all_data[index].append(center)
            all_data[index].append(triangle)
            all_data[index].append(points)
            all_data[index].append(score)
    
    #if an index is chosen, just create the list for that one place       
    else:
        all_data = all_data[country_index]
        points = sf.shapes()[country_index].points
        center = Polygon(points).centroid.coords[0]
        poly_area = Polygon(points).area
        #only want points from on convex shell
        convex_shell = convex_hull(points)
        triangle = find_points(convex_shell)
        score = round(triangle_area(triangle)/poly_area ,3)
        all_data.append(center)
        all_data.append(triangle)
        all_data.append(points)
        all_data.append(score)

    """
        all_data has the form of
[['name',(centerx,centery),[(tript1),(tript2),(tript3)],[(x1,y1),(x2,y2)..],SCORE]...]
    SCORE for now will be area of triangle/area of country
    """

    return all_data

#plot data should be called with just one countries info
def plot_data(country_data, directory='/Users/andrewlindstrom/Desktop'):
    country_name = country_data[0]
    center = country_data[1]
    triangle = country_data[2]
    other_points = country_data[3]
    score = country_data[4]

    #prepare triangle for plotting - note need to visit first point twice for good triangle
    unzip_tri = list(zip(*triangle))
    xtri, ytri = list(unzip_tri[0]), list(unzip_tri[1])
    xtri.append(xtri[0])
    ytri.append(ytri[0])
    
    #prepare normal perimiter points for plotting
    unzip_others = list(zip(*other_points))
    xvals, yvals = unzip_others[0], unzip_others[1]

    import matplotlib.pyplot as plt
    plt.figure()
    ax = plt.gca()
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    plt.plot(xvals, yvals,'k')
    plt.plot(xtri, ytri)
    plt.plot(center[0],center[1], 'ro', markersize = 5)
    plt.title(country_name)

    #change directory for where image is outputted
    file_name = country_name + ' ' + str(score) + '.png'
    os.chdir(directory)
    plt.savefig(file_name)
    plt.close()
