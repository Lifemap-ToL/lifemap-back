# FEV, 5 2016
# WE REMOVE THE WRITING TO JSON AND trees. This is performed by another code.
# This code is more complete than the previous one.
# I switched to ete3
# We read the tree from external file (trees are retrieved with the code called "gettrees.py").
# Added possibility to have groups containing only one descendants to be visible. Adds a few zoom levels (not so many)

# new
import logging
import math
import os
from typing import Literal
from pathlib import Path

import numpy as np
import psycopg  ##for postgresql connection

# import cPickle as pickle
from config import TAXO_DIRECTORY, PSYCOPG_CONNECT_URL, BUILD_DIRECTORY
from getTrees_fun import getTheTrees
from utils import download_file_if_newer

# print args

logger = logging.getLogger("LifemapBuilder")


def midpoint(x1, y1, x2, y2):
    # Input values as degrees
    # Convert to radians
    lat1 = math.radians(x1)
    lon1 = math.radians(y1)
    lat2 = math.radians(x2)
    lon2 = math.radians(y2)
    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat3 = math.atan2(
        math.sin(lat1) + math.sin(lat2),
        math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) + bx) + by**2),
    )
    lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)
    return [math.degrees(lat3), math.degrees(lon3)]


##update db (if requested?)
def updateDB():
    logger.info("Updating databases...")
    downloaded = download_file_if_newer(
        host="ftp.ncbi.nlm.nih.gov",
        remote_file="/pub/taxonomy/taxdump.tar.gz",
        local_file=TAXO_DIRECTORY / "taxdump.tar.gz",
    )
    # os.system("wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz -N")
    if downloaded:
        os.system(f"tar xvzf {TAXO_DIRECTORY / 'taxdump.tar.gz'} -C {TAXO_DIRECTORY}")
    # unzip taxref
    if not Path(TAXO_DIRECTORY / "TAXREFv11.txt").exists():
        os.system(
            f"unzip -o {TAXO_DIRECTORY / 'TAXREF_INPN_v11.zip'} -d {TAXO_DIRECTORY}"
        )


def simplify_tree(arbre):
    initialSize = len(arbre)
    for n in arbre.traverse():
        if n.is_leaf() and (n.rank == "no rank"):
            n.detach()
        else:
            if (
                ("Unclassified" in n.sci_name)
                or ("unclassified" in n.sci_name)
                or ("uncultured" in n.sci_name)
                or ("Uncultured" in n.sci_name)
                or ("unidentified" in n.sci_name)
                or ("Unidentified" in n.sci_name)
                or ("environmental" in n.sci_name)
                or ("sp." in n.sci_name)
            ):
                n.detach()
    logger.info("Tree HAS BEEN simplified")
    finalSize = len(arbre)
    diffInSize = initialSize - finalSize
    logger.info(
        str(diffInSize)
        + " tips have been removed ("
        + str(round(float(diffInSize) / float(initialSize) * 100, 2))
        + "%)"
    )
    logger.info("FINAL TREE SIZE: " + str(finalSize))
    return arbre


##FUNCTIONS
def rad(deg):
    return (deg * np.pi) / 180


def halfCircle(x, y, r, start, end, nsteps):
    rs = np.linspace(start, end, num=nsteps)
    xc = x + r * np.cos(rs)
    yc = y + r * np.sin(rs)
    return (xc, yc)


def ellipse(x, y, r, alpha, nsteps):
    start = 0
    end = np.pi + start
    rs = np.linspace(start, end, num=nsteps)
    a = r
    b = (
        float(r) / 6
    )  ##Change this value to change the shape of polygons. This controls how flat is the elliptic side of the polygon. The other side is always a half cricle.
    xs = a * np.cos(rs)
    ys = b * np.sin(rs)
    ##rotation
    xs2 = x + (xs * np.cos(alpha) - ys * np.sin(alpha))
    ys2 = y + (xs * np.sin(alpha) + ys * np.cos(alpha))
    return (xs2, ys2)


def HalfCircPlusEllips(x, y, r, alpha, start, end, nsteps):
    circ = halfCircle(x, y, r, start, end, nsteps)
    elli = ellipse(x, y, r, alpha, nsteps)
    return (np.concatenate((circ[0], elli[0])), np.concatenate((circ[1], elli[1])))


def writeosmNode(node, cur):
    ##we write INFO FOR EACH NODE. Clades will be delt with later on. We put less info than for the json file
    command = (
        "INSERT INTO points (id, taxid, sci_name, common_name,rank,nbdesc,zoomview, tip,way) VALUES(%d,%s,'%s','%s','%s',%d,%d,'%s',ST_Transform(ST_GeomFromText('POINT(%.20f %.20f)', 4326), 3857));"
        % (
            node.id,
            node.taxid,
            node.sci_name,
            node.common_name,
            node.rank,
            node.nbdesc,
            node.zoomview,
            node.is_leaf(),
            node.x,
            node.y,
        )
    )
    cur.execute(command)
    ##conn.commit();
    ##write json for search


def writeosmWays(node, id, cur, groupnb):
    # Create branch names
    Upsci_name = node.up.sci_name
    Upcommon_name = node.up.common_name
    Downsci_name = node.sci_name
    Downcommon_name = node.common_name
    left = Upsci_name + " " + Upcommon_name
    right = Downsci_name + " " + Downcommon_name
    if node.x >= node.up.x:  # we are on the right
        wayName = "\\u2190  " + left + "     -     " + right + "  \\u2192"
    else:  # we are on the left
        wayName = "\\u2190  " + right + "     -     " + left + "  \\u2192"

    ##new with midpoints:
    midlatlon = midpoint(node.up.x, node.up.y, node.x, node.y)

    command = (
        "INSERT INTO lines (id, branch, zoomview, ref, name, way) VALUES(%d,'TRUE',%d,'%s',E'%s',ST_Transform(ST_GeomFromText('LINESTRING(%.20f %.20f, %.20f %.20f,%.20f %.20f)', 4326), 3857));"
        % (
            id,
            node.zoomview,
            groupnb,
            wayName,
            node.up.x,
            node.up.y,
            midlatlon[0],
            midlatlon[1],
            node.x,
            node.y,
        )
    )
    cur.execute(command)
    ##conn.commit();


def writeosmpolyg(node, ids, cur, groupnb):
    polyg = HalfCircPlusEllips(
        node.x,
        node.y,
        node.ray,
        rad(node.alpha) + np.pi / 2,
        rad(node.alpha) - np.pi / 2,
        rad(node.alpha) + np.pi / 2,
        30,
    )
    polygcenter = (np.mean(polyg[0]), np.mean(polyg[1]))
    cooPolyg = "POLYGON((%.20f %.20f " % (polyg[0][0], polyg[1][0])
    for i in range(1, 59):
        cooPolyg += ",%.20f %.20f" % (polyg[0][i], polyg[1][i])
    cooPolyg += ",%.20f %.20f" % (polyg[0][0], polyg[1][0])
    # to close the ring...
    cooPolyg += "))"
    command = (
        "INSERT INTO polygons (id, ref, clade, taxid, sci_name, common_name, rank, nbdesc,zoomview, way) VALUES(%d,'%s','TRUE', %s,'%s','%s','%s',%d,%d, ST_Transform(ST_GeomFromText('%s', 4326), 3857));"
        % (
            ids[60],
            groupnb,
            node.taxid,
            node.sci_name,
            node.common_name,
            node.rank,
            node.nbdesc,
            node.zoomview,
            cooPolyg,
        )
    )
    cur.execute(command)
    ##conn.commit();
    # and add the clade center.
    command = (
        "INSERT INTO points (id, cladecenter, taxid, sci_name, common_name,rank,nbdesc,zoomview, way) VALUES('%d','TRUE', %s,'%s','%s','%s',%d,%d,ST_Transform(ST_GeomFromText('POINT(%.20f %.20f)', 4326), 3857));"
        % (
            ids[61],
            node.taxid,
            node.sci_name,
            node.common_name,
            node.rank,
            node.nbdesc,
            node.zoomview,
            polygcenter[0],
            polygcenter[1],
        )
    )
    cur.execute(command)
    ##conn.commit();
    # we add a way on which we will write the rank
    cooLine = "LINESTRING(%.20f %.20f" % (polyg[0][35], polyg[1][35])
    for i in range(36, 45):
        cooLine += ",%.20f %.20f" % (polyg[0][i], polyg[1][i])
    cooLine += ")"
    command = (
        "INSERT INTO lines (id, ref, rankname, sci_name, zoomview, rank, nbdesc, way) VALUES(%d,%s,'TRUE','%s',%d,'%s',%d, ST_Transform(ST_GeomFromText('%s', 4326), 3857));"
        % (
            ids[62],
            groupnb,
            node.sci_name,
            node.zoomview,
            node.rank,
            node.nbdesc,
            cooLine,
        )
    )
    cur.execute(command)
    ##conn.commit();


def writejsonNode(node, json):
    sci_name = node.sci_name
    sci_name = sci_name.replace('"', '\\"')
    common_name = node.common_name_long
    common_name = common_name.replace('"', '\\"')
    ##new attributes
    authority = node.authority
    authority = authority.replace('"', '\\"')
    synonym = node.synonym
    synonym = synonym.replace('"', '\\"')
    json.write("  {\n")
    json.write('    "taxid":"%s",\n' % (node.taxid))
    json.write('    "sci_name":"%s",\n' % (sci_name))
    json.write('    "common_name":"%s",\n' % (common_name))
    # new functions: add authority and synonym
    json.write('    "authority":"%s",\n' % (authority))
    json.write('    "synonym":"%s",\n' % (synonym))
    # end
    json.write('    "rank":"%s",\n' % (node.rank))
    json.write('    "zoom":"%d",\n' % (node.zoomview + 4))
    json.write('    "nbdesc":"%d",\n' % (node.nbdesc))
    json.write(
        '    "all":"%s | %s | %s | %s",\n'
        % (sci_name, common_name, node.rank, node.taxid)
    )
    json.write('    "coordinates": [%.20f,%.20f],\n' % (node.y, node.x))
    json.write('    "lat": "%.20f",\n' % (node.y))
    json.write('    "lon": "%.20f"\n' % (node.x))
    json.write("  },\n")


def traverse_tree(
    groupnb: Literal["1", "2", "3"],
    starti: int,
    lang: Literal["EN", "FR"] = "EN",
    updatedb: bool = True,
    simplify: bool = False,
) -> int:
    """
    Open taxonomic tree and recode it into PostGRES/PostGIS database for visualisation in Lifemap.

    Parameters
    ----------
    groupnb : {'1', '2', '3'}
        Group to look at. Can be 1,2 or 3 for Archaea, Eukaryotes and Bacteria respectively
    starti : int
        index of the first node met in the tree
    lang : {'EN', 'FR'}, optional
        Language chosen. FR for french, EN (default) for english, by default "EN"
    updatedb : bool, optional
        Should the NCBI taxonomy db be updated ?, by default True
    simplify : bool, optional
        Should the tree be simplified by removing environmental and unindentified species?, by default False

    Returns
    -------
    int
        ndid
    """

    if updatedb:
        logger.info("Updating database...")
        updateDB()
        logger.info("Done")
    T = getTheTrees()

    ##let's try to write the tree entirely here, in a file

    logger.info("Downloading tree...")
    if groupnb == "1":
        # with open('ARCHAEA.pkl', 'rb') as input:
        # t = pickle.load(input)
        t = T["2157"].detach()
        # SIMPLIFY THE TREE IF REQUESTED
        if simplify:
            t = simplify_tree(t)
        # t = Tree("ARCHAEA")
        logger.info("Archaeal tree loaded...")
        ##and we save it
        t.write(
            outfile=BUILD_DIRECTORY / "ARCHAEA",
            features=["name", "taxid"],
            format_root_node=True,
        )
        t.x = 6.0
        t.y = 9.660254 - 10.0
        t.alpha = 30.0
        t.ray = 10.0
        starti = starti
    if groupnb == "2":
        # with open('EUKARYOTES.pkl', 'rb') as input:
        # 	t = pickle.load(input)
        t = T["2759"].detach()
        # SIMPLIFY THE TREE IF REQUESTED
        if simplify:
            t = simplify_tree(t)
        logger.info("Eukaryotic tree loaded")
        t.write(
            outfile=BUILD_DIRECTORY / "EUKARYOTES",
            features=["name", "taxid"],
            format_root_node=True,
        )
        t.x = -6.0
        t.y = 9.660254 - 10.0
        t.alpha = 150.0
        t.ray = 10.0
        starti = starti
    if groupnb == "3":
        # with open('BACTERIA.pkl', 'rb') as input:
        # 	t = pickle.load(input)
        t = T["2"].detach()
        # SIMPLIFY THE TREE IF REQUESTED
        if simplify:
            t = simplify_tree(t)
        logger.info("Bacterial tree loaded")
        t.write(
            outfile=BUILD_DIRECTORY / "BACTERIA",
            features=["name", "taxid"],
            format_root_node=True,
        )
        t.x = 0.0
        t.y = -11.0
        t.alpha = 270.0
        t.ray = 10.0
        starti = starti

    t.zoomview = np.ceil(np.log2(30 / t.ray))

    # specis and node ids
    nbsp = len(t)
    spid = starti
    ndid = starti + nbsp
    maxZoomView = 0

    ##CONNECT TO POSTGRESQL/POSTGIS DATABASE
    try:
        conn = psycopg.connect(
            PSYCOPG_CONNECT_URL
        )  # password will be directly retrieved from ~/.pgpassconn
    except Exception as e:
        raise RuntimeError(f"Unable to connect to the database: {e}")

    cur = conn.cursor()
    ##INITIALIZE DATABASE
    if groupnb == "1":
        ##we delete current tables
        logger.info("REMOVING OLD TABLES")
        cur.execute("DROP TABLE IF EXISTS points;")
        cur.execute("DROP TABLE IF EXISTS lines;")
        cur.execute("DROP TABLE IF EXISTS polygons;")
        conn.commit()
        ##we create the database structure here
        cur.execute(
            "CREATE TABLE points(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankame boolean,sci_name text,common_name text,full_name text,rank text, name text, nbdesc integer,taxid text,way geometry(POINT,3857));"
        )
        cur.execute(
            "CREATE TABLE lines(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankname boolean,sci_name text,common_name text,full_name text,rank text,name text, nbdesc integer,taxid text,way geometry(LINESTRING,3857));"
        )
        cur.execute(
            "CREATE TABLE polygons(id bigint,ref smallint,z_order smallint,branch boolean,tip boolean,zoomview integer,clade boolean,cladecenter boolean,rankame boolean,sci_name text,common_name text,full_name text,rank text, name text, nbdesc integer,taxid text,way geometry(POLYGON,3857));"
        )
        conn.commit()
        logger.info("\nTABLES HAVE BEEN CREATED. Done.\n")
        ##we include the root node
        cur.execute(
            "INSERT INTO points (id, sci_name, common_name,rank,nbdesc,tip, zoomview,taxid,way) VALUES(1000000000, 'Root','Root','Root',1000000, FALSE, 1,1,ST_Transform(ST_GeomFromText('POINT(0 -4.226497)', 4326), 3857));"
        )
        conn.commit()

    logger.info("Tree traversal...")
    for n in t.traverse():
        special = 0
        n.dist = 1.0
        tot = 0.0
        if n.is_leaf():
            spid = spid + 1
            n.id = spid
        else:
            ndid = ndid + 1
            n.id = ndid
        child = n.children
        ##NEW  -->|
        if (len(child) == 1) & (len(n) > 1):
            special = 1
        if (len(child) == 1) & (len(n) == 1):
            special = 2
        ## |<-- NEW
        for i in child:
            tot = tot + np.sqrt(len(i))
        nbdesc = len(n)
        ##remove special chars in names
        ####IF --LANG IS SET TO FR, WE CHGANGE HERE THE RANK AND COMMON NAMES
        if lang == "FR":
            n.common_name = n.common_name_FR
            n.rank = n.rank_FR
        #####OK
        n.common_name_long = ", ".join(n.common_name)
        n.common_name = n.common_name[0] if len(n.common_name) > 0 else ""
        ##we create a 'long' common name. the common name going to db is only the first of the list
        n.common_name = n.common_name.replace("'", "''")
        n.rank = n.rank.replace("'", "''")
        n.sci_name = n.sci_name.replace("'", "''")
        # add parenthesis to the common name
        if n.common_name != "":
            n.common_name = "(" + n.common_name + ")"
        if n.common_name_long != "":
            n.common_name_long = "(" + n.common_name_long + ")"
        n.nbdesc = nbdesc
        angles = []
        ray = n.ray
        for i in child:
            # i.ang = 180*(len(i)/float(nbdesc))/2;
            i.ang = 180 * (np.sqrt(len(i)) / tot) / 2
            # using sqrt we decrease difference between large and small groups
            angles.append(i.ang)
            if special == 1:
                i.ray = ray - (ray * 20) / 100
            else:
                if special == 2:
                    i.ray = ray - (ray * 50) / 100
                else:
                    i.ray = (ray * np.sin(rad(i.ang)) / np.cos(rad(i.ang))) / (
                        1 + (np.sin(rad(i.ang)) / np.cos(rad(i.ang)))
                    )
            i.dist = ray - i.ray
        ang = np.repeat(angles, 2)
        ang = np.cumsum(ang)
        ang = ang[0::2]
        ang = [i - (90 - n.alpha) for i in ang]
        cpt = 0
        for i in child:
            i.alpha = ang[cpt]
            i.x = n.x + i.dist * np.cos(rad(i.alpha))
            i.y = n.y + i.dist * np.sin(rad(i.alpha))
            i.zoomview = np.ceil(np.log2(30 / i.ray))
            if i.zoomview <= 0:
                i.zoomview = 0
            if maxZoomView < i.zoomview:
                maxZoomView = i.zoomview
            cpt = cpt + 1
        # we write node info
        writeosmNode(n, cur)

    logger.info("Tree traversal... DONE (first one)")
    conn.commit()

    #################################
    #       WRITE JSON FILES        #
    #################################
    jsonfile = BUILD_DIRECTORY / f"TreeFeatures{groupnb}.json"
    with open(jsonfile, "w") as json:
        json.write("[\n")

        logger.info("Tree traversal 2... ")
        ##LAST LOOP TO write coords of polygs and JSON file
        for n in t.traverse():
            # save all trees to disk
            #    out="trees/" + str(n.taxid) + ".tre";
            #    n.write(outfile=out, features=["taxid","sci_name","common_name","rank"]);
            ##we finish writing in the database here.
            if not n.is_root():
                ndid = ndid + 1
                writeosmWays(n, ndid, cur, groupnb)
            if not n.is_leaf():
                indexes = np.linspace(ndid + 1, ndid + 63, num=63)
                writeosmpolyg(n, indexes, cur, groupnb)
                ndid = ndid + 63
            writejsonNode(n, json)
        ##after this, node.nbgenomes should be ok.
        logger.info("Tree traversal 2... DONE ")
        conn.commit()

        ##we add the way from LUCA to the root of the subtree
        ndid = ndid + 1
        command = (
            "INSERT INTO lines (id, branch, zoomview, ref, way) VALUES(%d,'TRUE', '4','%s',ST_Transform(ST_GeomFromText('LINESTRING(0 -4.226497, %.20f %.20f)', 4326), 3857));"
            % (ndid, groupnb, t.x, t.y)
        )
        cur.execute(command)
        conn.commit()

        logger.info(f"DONE - ndid:{ndid} - spid:{spid} - Max zoom view: {maxZoomView}")

    ##remove unwanted last character(,) of json file
    consoleexex = (
        "head -n -1 " + str(jsonfile) + " > temp.txt ; mv temp.txt " + str(jsonfile)
    )
    os.system(consoleexex)
    with open(jsonfile, "a") as json:
        json.write("\t}\n]\n")

    return ndid
