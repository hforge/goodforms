# -*- coding: UTF-8 -*-

# Import from itools
from itools.gettext import MSG

#####################################################
# Emails sent to workgroup administrators when
# nb_forms has reached some limits.
#####################################################

# TODO: Write a better mail

email_credit_alert_subject = MSG(u"Numbers of allowed users has reached a limit")
email_credit_alert_text = MSG(u"""Hi {user_title},\n
Workgroup title: {workgroup_title}\n
You application "{application_title}" has reached a limit.\n
There's only {nb_forms}/{max_users}\n
So it's remaining only {remaining_users} users\n
You can order new credit here:\n
  {order_uri}\n
See you !
""")

email_credit_alert = {'subject': email_credit_alert_subject,
                      'text': email_credit_alert_text}
