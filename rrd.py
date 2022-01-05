#!/usr/bin/env python3

import os
try:
    import dict2xml
    import xmltodict
except (NameError, ImportError) as e:
    print("Please install: \n pip3 install dict2xml xmltodict")
    exit(0)
import datetime
import argparse
from subprocess import run
from shutil import copyfile

var_time = datetime.datetime.now()
exec_time = var_time.strftime("%d-%m-%Y-%H-%M")


def rrd2xml(rrd_file):
    try:
        head, tail = os.path.split(rrd_file)
        copyfile(f"{rrd_file}", f"/tmp/{exec_time}-{tail}")
        out_xml_file_path = f"/tmp/{exec_time}-" + f"{tail}".replace("rrd", "xml")
        run(f"rrdtool dump {rrd_file} > {out_xml_file_path}", shell=True, check=True)
        return out_xml_file_path
    except FileNotFoundError as e:
        print(f"File I/O ERROR: {e}")


def scan(xml_file_path, limit):
    xml_file = open(xml_file_path, "r")
    data_dict = xmltodict.parse(xml_file.read())
    try:
        databases_counter = 0
        row_counter = 0
        fixed_dict = data_dict
        for database in range(databases_counter, len(data_dict["rrd"]["rra"])):
            for row in range(row_counter, len(data_dict["rrd"]["rra"][database]["database"]["row"])):
                if float(data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0]) >= float(limit):
                    with open(xml_file_path, "r") as f:
                        for line in f.readlines():
                            if data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0] in line:
                                print(line.lstrip().rstrip())
                if float(data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1]) >= float(limit):
                    with open(xml_file_path, "r") as f:
                        for line in f.readlines():
                            if data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1] in line:
                                print(line.lstrip().rstrip())

    except Exception as e:
        print(e)

def fix(xml_file_path, limit):
    xml_file = open(xml_file_path, "r")
    data_dict = xmltodict.parse(xml_file.read())
    try:
        # Счетчики указатели на текущую базу/строку.
        databases_counter = 0
        row_counter = 0
        fixed_dict = data_dict
        # Исправляем NaN
        for database in range(databases_counter, len(data_dict["rrd"]["rra"])):
            for row in range(row_counter, len(data_dict["rrd"]["rra"][database]["database"]["row"])):
                # in traffic NaN fix
                if data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0] == "NaN":
                    if row - 3 >= 0 and (row - 3 != "NaN" and row - 2 != "NaN" and row - 3 != "NaN"):
                        medium_value = float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 3]["v"][0]) + \
                                       float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 2]["v"][0]) + \
                                       float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 1]["v"][0])
                        # save
                        fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0] = '{0:.10e}'.format(
                            medium_value / 3)

                # out traffic NaN fix
                if data_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1] == "NaN":
                    if row - 3 >= 0 and (row - 3 != "NaN" and row - 2 != "NaN" and row - 3 != "NaN"):
                        medium_value = float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 3]["v"][1]) + \
                                       float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 2]["v"][1]) + \
                                       float(data_dict["rrd"]["rra"][database]["database"]["row"][row - 1]["v"][1])
                        # save
                        fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1] = '{0:.10e}'.format(
                            medium_value / 3)
        # Исправляем лимиты
        databases_counter = 0
        row_counter = 0
        for database in range(databases_counter, len(fixed_dict["rrd"]["rra"])):
            for row in range(row_counter, len(fixed_dict["rrd"]["rra"][database]["database"]["row"])):
                if float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0]) > float(limit):
                    print(dict(fixed_dict["rrd"]["rra"][database]["database"]["row"][row]))
                    medium_value = float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 3]["v"][0]) + \
                                   float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 2]["v"][0]) + \
                                   float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 1]["v"][0])
                    # save
                    fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][0] = '{0:.10e}'.format(
                        medium_value / 3)

                if float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1]) > float(limit):
                    print(dict(fixed_dict["rrd"]["rra"][database]["database"]["row"][row]))
                    medium_value = float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 3]["v"][1]) + \
                                   float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 2]["v"][1]) + \
                                   float(fixed_dict["rrd"]["rra"][database]["database"]["row"][row - 1]["v"][1])
                    # save
                    fixed_dict["rrd"]["rra"][database]["database"]["row"][row]["v"][1] = '{0:.10e}'.format(
                        medium_value / 3)

        xml = dict2xml.dict2xml(fixed_dict)
        with open(xml_file_path, "w") as f:
            f.write(xml)

    except IndexError as e:
        return print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NetOps Tool 80lvl.')
    parser.add_argument('-a', '--action', dest='action', required=True, default=None,
                        help='Actions: "fix" or "scan"')
    parser.add_argument('-l', '--limit', dest='limit', required=True, default=None,
                        help='Bandwidth limit: "2.3772817081e+10" or 2.3772817081e+10')
    parser.add_argument('-f', '--file', dest='file', required=True, default=None,
                        help='Input file to parse.')
    args = parser.parse_args()

    xml_path = rrd2xml(args.file)
    
    if args.action == "scan":
        scan(xml_file_path=xml_path, limit=args.limit)
    elif args.action == "fix":
        xml = fix(xml_file_path=xml_path, limit=args.limit)
        os.remove(args.file)
        run(f"rrdtool restore {xml_path} {args.file}", shell=True, check=True)

