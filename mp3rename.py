#!/usr/bin/env python3
#-*-coding: utf-8 -*-
#pylint: disable=W0141

import argparse
import os
import io
import shutil

#Dependencies:
#pip3 install pypinyin
#https://github.com/mozillazg/python-pinyin
import pypinyin 
#pip3 install eyeD3
#brew install libmagic
#https://eyed3.readthedocs.io/
import eyed3

mp3_keys = ["artist", "album", "album_artist", "title", "track_num"]

def normalizePinyinStr(mlst, sep=' '):
    lst = []
    for l in mlst:
        s = l[0]
        lst.append(s.capitalize())

    return sep.join(lst)


def readMp3(path, fn):
    needConvert = False

    py_fn = pypinyin.pinyin(fn, style=pypinyin.STYLE_NORMAL)
    if py_fn[0][0] != fn:
        needConvert = True
    else:
        print("Skip non-Chinese file: %s" % fn)
        return None
    if py_fn[-1][0] != ".mp3":
        print("Skip non-mp3 file: %s" % fn)
        return None

    mp3 = {}
    mp3["orig_path"] = path
    mp3["orig_fn"] =  fn
    mp3["new_fn"] = normalizePinyinStr(py_fn[:-1]) + ".mp3"

    id3 = eyed3.load(fn)

    mp3["artist"] = id3.tag.artist
    mp3["album"] = id3.tag.album
    mp3["album_artist"] = id3.tag.album_artist
    mp3["title"] = id3.tag.title
    mp3["track_num"] = id3.tag.track_num

    for k in mp3.keys():
        v = mp3[k]
        if v and type(v) is str:
            py = pypinyin.pinyin(v, style=pypinyin.STYLE_NORMAL)
            if py[0][0]!=v:
                needConvert = True

    if needConvert:
        return mp3
    else:
        return None

count = 0
def copyMp3(mp3, args):
    global count
    print("[%4d] Creating PINYIN version mp3 for: %s/%s to %s" %(count, mp3["orig_path"], mp3["orig_fn"], mp3["new_fn"]))

    target_fn =  "%s/%s"%(mp3["orig_path"], mp3["new_fn"])
    fn_parts = mp3["new_fn"].strip(".mp3").split("-")

    if args.short_fn and len(fn_parts)==2:
        title = fn_parts[1].strip()
        target_fn  = "%s/%s.mp3"%(mp3["orig_path"], title)

    shutil.copyfile("%s/%s"%(mp3["orig_path"], mp3["orig_fn"]), target_fn)
    id3 = eyed3.load(target_fn)

    if args.auto_author_title and len(fn_parts) == 2:
        id3.tag.artist = fn_parts[0].strip()
        id3.tag.title = fn_parts[1].strip()
    else:
        id3.tag.artist = pypinyin.slug(mp3["artist"])
        id3.tag.tilte = pypinyin.slug(mp3["title"])

    if args.album:
        id3.tag.album = args.album
    else:
        id3.tag.album = pypinyin.slug(mp3["album"])

    id3.tag.album_artist = None
    id3.tag.track_num = None

    id3.tag.save()
    print("[%4d] %s created successfully!\n"%(count, target_fn))
    count = count  + 1
    return

def convertOneMp3(path, fn, args):
    mp3 = readMp3(path, fn)
    if mp3:
        copyMp3(mp3, args)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="mp3rename.py")
    parser.add_argument("mp3list",  nargs="*", default=[], help="Mp3 file list")
    parser.add_argument("-ch2py", action="store_true", default=False, help="rename mp3 with chinese filename to Pinyin filename and also convert other Chinese fields to Pinyin in mp3 tag")
    parser.add_argument("-album", type=str, default=None, help="update album name")
    parser.add_argument("-auto_author_title", action="store_true", default=False, help="Update author and title based on filename. Filename must be separated by \"-\"")
    parser.add_argument("-short_fn", action="store_true", default=False, help="remove author name from the new file name")

    args = parser.parse_args()

    for mp3 in args.mp3list:
        path, fn = os.path.abspath(mp3).rsplit("/", maxsplit=1)
        convertOneMp3(path, fn, args)
