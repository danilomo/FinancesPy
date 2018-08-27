#!/usr/bin/env python

import sys
import os
import datetime
import itertools
import financespy.clutil as clutil
from financespy.clutil import Command
import financespy.sh as sh

from financespy.account import Account
from financespy.filesystem_backend import FilesystemBackend
from financespy.transaction import parse_transaction


def current_year():
    return datetime.datetime.now().year

def backend(folder):
    return FilesystemBackend( folder )

@Command
def import_csv( args, workspace = "./ws/", year = current_year() ):
    month = args[0]
    file_name = args[1]

    account = Account( backend(workspace) )

    with open( file_name, "r" ) as file_:

        for line in file_:
            columns = [line.strip() for line in line.split(",") if line.strip() ]
            day = int(columns[0])
            transaction = parse_transaction(columns[1:])

            if not transaction.value.is_zero():            
                account.day( day, month, year ).insert_record( transaction )
                
@Command
def review_month( args, workspace = "./ws/", year = current_year() ):

    month = args[0]
    account = Account( backend(workspace) )

    for day in account.month( month, year ).days():
        os.system('clear')
        print( "Day: " + str(day.date) )

        records = list( day.records() )

        if not records:
            print("No expenses.")
            input()
            continue

        records_as_str = [ str(r) for r in records ]
        maxlen         = len(max( records_as_str, key=len)) if records else 0
        hr             = maxlen * "_"

        print(hr + "\n")
        print( "\n".join(records_as_str) )
        print(hr)

        values = [ r.value for r in records ]
        total = sum(values)
        print("\nTotal: " + str(total) )

        input()


@Command
def edit_day( args,  editor = "emacs", workspace = "./ws/", year = current_year() ):
    day = int(args[0])
    month = args[1]
    year = int(year)

    account = Account( backend(workspace) )

    day = account.day( day, month, year )

    file_name = day.backend.file( day.date )

    if not os.path.exists(file_name):
        sh.touch(file_name)

    sh.emacs(file_name, _bg = True)

def main():
    clutil.execute()

if __name__ == "__main__":
    main()
