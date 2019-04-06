import bs4
import argparse
import urllib.request as urllib
import urllib.parse as urlparse
import os.path
import sys
import re
import datetime
import time
from hurry.filesize import size
import shutil


def get_html(url):
    try:
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
        req = urllib.Request(url, headers=hdr)
        res = urllib.urlopen(req)
        txt = res.read()
        txtstr = txt.decode("utf-8")
        return txtstr
    except:
        parser.print_help()
        sys.exit()


def get_board_name(url):
    path = urlparse.urlparse(url).path.split("/")[1]
    return '[' + path + ']'


def get_op(html):
    folder_name = ''
    soup = bs4.BeautifulSoup(html, 'html.parser')
    subjects = soup.find_all('span', {'class': 'subject'})
    subject = subjects[1].text
    op = soup.find('blockquote', {'class': 'postMessage'}).text
    if subject != "":
        subject = subject.replace("'", "")
        subject = re.sub(r"[^a-zA-Z0-9-!]+", ' ', subject)
        subject_words = subject.split(" ")
        folder_name += make_str(subject_words, True)
    else:
        op = op.replace("'", "")
        op = re.sub(r"[^a-zA-Z0-9-!]+", ' ', op)
        op_words = op.split(" ")
        folder_name += make_str(op_words, False)
    if folder_name[:1] == "_":
        return folder_name[1:-1]
    else:
        return folder_name[:-1]


def make_str(words, subject_bool):
    string = ''
    if not subject_bool:
        if len(words) < 7:
            for word in words:
                string += word + "_"
        else:
            for x in range(0, 7):
                string += words[x] + "_"
    else:
        for word in words:
            string += word + "_"
    return string


def get_download_links(html):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    event_cells = soup.find_all('div', {'class': 'fileText'})
    url_filename_dict = {}
    for e in event_cells:
        file_url = e.select('a')[0]['href']
        file_url = "https:" + file_url
        filename = e.select('a')[0]
        if filename.has_attr('title'):
            filename = filename['title']
        else:
            filename = filename.text
        if filename == "Spoiler Image":
            filename = e["title"]
        url_filename_dict.update({filename: file_url})
    return url_filename_dict


def check_dir(path, overwrite_bool):
    if not os.path.isdir(path):
        make_dir(path)
    else:
        if not overwrite_bool:
            print(
                "The directory already exsists. Would you like to remove it before downloading? y/n")
            answer = input()
            if answer == "y":
                remove_dir(path)
                make_dir(path)
            else:
                sys.exit()
        else:
            remove_dir(path)
            make_dir(path)


def make_dir(path):
    try:
        os.mkdir(path)
    except OSError:
        print("\nCreation of the directory %s failed\n" % path)
    else:
        print("\nSuccessfully created the directory %s \n" % path)


def remove_dir(path):
    try:
        shutil.rmtree(path)
    except OSError:
        print("\nRemoval of the directory %s failed\n" % path)
    else:
        print("\nSuccessfully removed the directory %s \n" % path)


def get_time(seconds):
    print("\nIt took " + str(datetime.timedelta(seconds=seconds))
          [:-4] + " to download the files.")


def calc_dir_size(dir_path, list_bool):
    folder_size = 0
    for (path, dirs, files) in os.walk(dir_path):
        for file in files:
            filename = os.path.join(path, file)
            folder_size += os.path.getsize(filename)
    if list_bool:
        return folder_size
    else:
        return size(folder_size)


def download_files(links_and_filenames_dict, directory, url, list_bool, time_bool, overwrite_bool):
    start = time.time()
    path = get_board_name(url) + get_op(get_html(url)) + '/'
    if directory == None:
        check_dir(path, overwrite_bool)
    else:
        path = directory + path
        check_dir(path, overwrite_bool)
    for filename_key, url_value in links_and_filenames_dict.items():
        try:
            with urllib.urlopen(url_value) as dlFile:
                content = dlFile.read()
                filename = filename_key.replace('?', '')
                complete_name = os.path.join(path + filename)
                file = open(complete_name, "wb")
                file.write(content)
                file.close
            print(url_value + " was saved as " + filename)
        except Exception as e:
            print(e)
    end = time.time()
    total_time = end - start
    if time_bool:
        get_time(total_time)
    if not list_bool:
        print("\nThe downloaded files took up " +
              calc_dir_size(path, list_bool) + " of your harddisk space.")
    else:
        return calc_dir_size(path, list_bool)


if __name__ == '__main__':
    disk_space = 0
    parser = argparse.ArgumentParser(
        description='A script that downloads all media files from a 4chan thread')
    parser.add_argument(
        '-u', '--url', help='URL for the 4chan thread you want to download the files from')
    parser.add_argument('-d', '--destination', help='The absolute path to the directory you want the new folder with the downloaded files to be stored in. NOTE: If left blank, a new directory will be created in the active directory from where you are running the script.')
    parser.add_argument(
        '-l', '--list', help="List of thread URL's you want to download the files from", type=str)
    parser.add_argument(
        '-o', '--overwrite', help='Automatically overwrites any folders with the same name as the folders being created by the script', action='store_true')
    args = parser.parse_args()
    if args.url == None:
        parser.print_help()
        sys.exit()
    if args.url == "test":
        print("URL: " + str(args.url))
        print("Destination: " + str(args.destination))
        print("URL List:" + str(args.list))
        sys.exit()
    dest = args.destination
    if dest != None:
        if dest[-1:] != "/" or dest[-1:] != "\\":
            dest = dest + "/"
    if args.list != None:
        start = time.time()
        url_list = [str(item) for item in args.list.split(' ')]
        for url in url_list:
            disk_space += download_files(get_download_links(get_html(url)),
                                         dest, url, True, False, args.overwrite)
        end = time.time()
        total_time = end - start
        get_time(total_time)
    else:
        download_files(get_download_links(get_html(args.url)),
                       dest, args.url, False, True, args.overwrite)
    if disk_space > 0:
        print("\nThe downloaded files took up " +
              size(disk_space) + " of your harddisk space.")
