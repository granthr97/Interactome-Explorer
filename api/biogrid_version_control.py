import requests
import os
import glob
import zipfile
import shutil
import data.makegraphs as makegraphs

BIOGRID_KEY = "39557a40f8059e8b4adbf4e0286cd02b"
BIOGRID_URL = "https://webservice.thebiogrid.org/version?accesskey={}".format(
    BIOGRID_KEY)
BIOGRID_TAB2_URL = "https://downloads.thebiogrid.org/Download/BioGRID/Release-Archive/BIOGRID-{}/BIOGRID-ALL-{}.tab2.zip"
DATA_DIR = os.path.abspath("data")


def get_current_version():
    r = requests.get(BIOGRID_URL)
    return r.content.decode().strip()


def get_latest_local_version():
    latest_version = os.path.basename(
        sorted(glob.glob("{}/*_graphs".format(DATA_DIR)))[-1]).split("_")[0]
    return latest_version.strip()


def download_biogrid_tab2_file(version):
    filename = "{}/{}_tab2.zip".format(DATA_DIR, version)
    url = BIOGRID_TAB2_URL.format(version, version)
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)
    return filename


def unzip_and_save_biogrid_tab2_file(filename):
    if os.path.exists("temp"):
        shutil.rmtree("temp")
    os.mkdir("temp")
    unziped_filename = "{}.txt".format(filename[:-4])
    with zipfile.ZipFile(filename) as f:
        f.extractall("temp")
    shutil.copyfile(glob.glob("temp/**")[0], unziped_filename)
    shutil.rmtree("temp")
    return unziped_filename


def create_and_save_pickle_file(filename):
    version = os.path.basename(filename).split("_")[0]
    graphs_dir = "{}/{}_graphs/".format(DATA_DIR, version)
    os.mkdir(graphs_dir)
    makegraphs.set_graph_from_file(filename, graphs_dir)
