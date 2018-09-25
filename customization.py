# -*- coding: UTF-8 -*-


# Quick customization engine

__custom_flags = {
    # in application_views.py : if True, add a header row in result table with
    # data types of each column.
    'header_data_type' : False,

    # in forms_view.py, Form_send : if True, do not show warning about invalid
    # fields if field is empty and not mandatory (less warnings for big tables)
    'hide_invalid_empty' : True
    }

# function to be called by goodforms modules when asking for an option :
def custom_flag(value):
    return __custom_flags.get(value, False)

# simple test of config :
if __name__ == '__main__':
    print "list current key/value for custom_flag() :"
    for key, value in __custom_flags.iteritems():
        print key, ":", value
