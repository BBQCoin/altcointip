"""
    This file is part of ALTcointip.

    ALTcointip is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ALTcointip is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ALTcointip.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging, re, time
import ctb_misc

lg = logging.getLogger('cointipbot')

def update_stats(ctb=None):
    """
    Update stats wiki page
    """

    stats = ""

    if not ctb.conf.reddit.stats.enabled:
        return None

    for s in sorted(vars(ctb.conf.db.sql.globalstats)):
        lg.debug("update_stats(): getting stats for '%s'" % s)
        sql = ctb.conf.db.sql.globalstats[s].query
        stats += "\n\n### %s\n\n" % ctb.conf.db.sql.globalstats[s].name
        stats += "%s\n\n" % ctb.conf.db.sql.globalstats[s].desc

        mysqlexec = ctb.db.execute(sql)
        if mysqlexec.rowcount <= 0:
            lg.warning("update_stats(): query <%s> returned nothing" % ctb.conf.db.sql.globalstats[s].query)
            continue

        if ctb.conf.db.sql.globalstats[s].type == "line":
            m = mysqlexec.fetchone()
            k = mysqlexec.keys()[0]
            if k.find("usd") > -1:
                stats += "%s = **$%.2f**\n" % (k, m[k])
            else:
                stats += "%s = **%s**\n" % (k, m[k])
        elif ctb.conf.db.sql.globalstats[s].type == "table":
            stats += ("|".join(mysqlexec.keys())) + "\n"
            stats += ("|".join([":---"] * len(mysqlexec.keys()))) + "\n"
            for m in mysqlexec:
                values = []
                for k in mysqlexec.keys():
                    if type(m[k]) == float and k.find("coin") > -1:
                        values.append("%.8g" % m[k])
                    elif type(m[k]) == float and k.find("fiat") > -1:
                        values.append("$%.2f" % m[k])
                    elif k.find("user") > -1:
                        if m[k] != None:
                            values.append("/u/%s ^[[stats]](/r/%s/wiki/%s_%s)" % (m[k], ctb.conf.reddit.stats.subreddit, ctb.conf.reddit.stats.page, m[k]))
                        else:
                            values.append("None")
                    elif k.find("subreddit") > -1:
                        values.append("/r/" + str(m[k]))
                    elif k.find("link") > -1:
                        values.append("[link](%s)" % m[k])
                    else:
                        values.append(str(m[k]))
                stats += ("|".join(values)) + "\n"
        else:
            lg.error("update_stats(): don't know what to do with type '%s'" % ctb.conf.db.sql.globalstats[s].type)
            return False

        stats += "\n"

    lg.debug("update_stats(): updating subreddit '%s', page '%s'" % (ctb.conf.reddit.stats.subreddit, ctb.conf.reddit.stats.page))
    return ctb_misc.praw_call(ctb.reddit.edit_wiki_page, ctb.conf.reddit.stats.subreddit, ctb.conf.reddit.stats.page, stats, "Update by ALTcointip bot")

def update_all_user_stats(ctb=None):
    """
    Update individual user stats for all uers
    """

    if not ctb.conf.reddit.stats.enabled:
        lg.error('update_all_user_stats(): stats are not enabled in config.yml')
        return None

    users = ctb.db.execute(ctb.conf.db.sql.userstats.users)
    for u in users:
        update_user_stats(ctb=ctb, username=u['username'])

def update_user_stats(ctb=None, username=None):
    """
    Update individual user stats for given username
    """

    if not ctb.conf.reddit.stats.enabled:
        return None

    # Build a list of coins
    coins_q = ctb.db.execute(ctb.conf.db.sql.userstats.coins)
    coins = []

    for c in coins_q:
        coins.append(c['coin'])

        user_stats = "### Tipping Summary For /u/%s\n\n" % username
        page = ctb.conf.reddit.stats.page + '_' + username

        # Total Tipped
        user_stats += "#### Total Tipped (USD)\n\n"
        mysqlexec = ctb.db.execute(ctb.conf.db.sql.userstats.total_tipped_fiat, (username))
        total_tipped_fiat = mysqlexec.fetchone()
        if total_tipped_fiat['total_fiat'] == None:
            user_stats += "**total_tipped_fiat = $%.2f**\n\n" % 0.0
        else:
            user_stats += "**total_tipped_fiat = $%.2f**\n\n" % total_tipped_fiat['total_fiat']

        user_stats += "#### Total Tipped (Coins)\n\n"
        user_stats += "coin|total\n:---|---:\n"
        for c in coins:
            mysqlexec = ctb.db.execute(ctb.conf.db.sql.userstats.total_tipped_coin, (username, c))
            total_tipped_coin = mysqlexec.fetchone()
            if total_tipped_coin['total_coin'] == None:
                user_stats += "%s|%.8g\n" % (c, 0.0)
            else:
                user_stats += "%s|%.8g\n" % (c, total_tipped_coin['total_coin'])
        user_stats += "\n"

        # Total received
        user_stats += "#### Total Received (USD)\n\n"
        mysqlexec = ctb.db.execute(ctb.conf.db.sql.userstats.total_received_fiat, (username))
        total_received_fiat = mysqlexec.fetchone()
        if total_received_fiat['total_fiat'] == None:
            user_stats += "**total_received_fiat = $%.2f**\n\n" % 0.0
        else:
            user_stats += "**total_received_fiat = $%.2f**\n\n" % total_received_fiat['total_fiat']

        user_stats += "#### Total Received (Coins)\n\n"
        user_stats += "coin|total\n:---|---:\n"
        for c in coins:
            mysqlexec = ctb.db.execute(ctb.conf.db.sql.userstats.total_received_coin, (username, c))
            total_received_coin = mysqlexec.fetchone()
            if total_received_coin['total_coin'] == None:
                user_stats += "%s|%.8g\n" % (c, 0.0)
            else:
                user_stats += "%s|%.8g\n" % (c, total_received_coin['total_coin'])
        user_stats += "\n"

        # History
        user_stats += "#### History\n\n"
        history = ctb.db.execute(ctb.conf.db.sql.userstats.history, (username, username))
        user_stats += ("|".join(history.keys())) + "\n"
        user_stats += ("|".join([":---"] * len(history.keys()))) + "\n"

        # Build history table
        for m in history:
            values = []
            for k in history.keys():
                # Format cryptocoin
                if type(m[k]) == float and k.find("coin") > -1:
                    coin_symbol = ctb.conf.coins[m['coin']].symbol
                    values.append("%s%.8g" % (coin_symbol, m[k]))
                # Format fiat
                elif type(m[k]) == float and k.find("fiat") > -1:
                    fiat_symbol = ctb.conf.fiat[m['fiat']].symbol
                    values.append("%s%.2f" % (fiat_symbol, m[k]))
                # Format username
                elif k.find("user") > -1:
                    if m[k] != None:
                        un = ("**%s**" % username) if m[k].lower() == username.lower() else m[k]
                        toappend = "[%s](/u/%s)" % (un, re.escape(m[k]))
                        if m[k].lower() != username.lower():
                            toappend += " ^[[stats]](/r/%s/wiki/%s_%s)" % (ctb.conf.reddit.stats.subreddit, ctb.conf.reddit.stats.page, m[k])
                        values.append(toappend)
                    else:
                        values.append("None")
                # Format address
                elif k.find("addr") > -1:
                    if m[k] != None:
                        displayaddr = m[k][:6] + "..." + m[k][-5:]
                        values.append("[%s](%s)" % (displayaddr, ctb.conf.coins[m['coin']].explorer.address + m[k]))
                    else:
                        values.append("None")
                # Format state
                elif k.find("state") > -1:
                    if m[k] == "completed":
                        values.append("**%s**" % m[k])
                    else:
                        values.append(m[k])
                # Format subreddit
                elif k.find("subreddit") > -1:
                    values.append("/r/" + str(m[k]))
                # Format link
                elif k.find("link") > -1:
                    values.append("[link](%s)" % m[k])
                # Format time
                elif k.find("utc") > -1:
                    values.append("%s" % time.strftime('%Y-%m-%d', time.localtime(m[k])))
                else:
                    values.append(str(m[k]))

            user_stats += ("|".join(values)) + "\n"

    lg.debug("update_user_stats(): updating subreddit '%s', page '%s'" % (ctb.conf.reddit.stats.subreddit, page))
    ctb_misc.praw_call(ctb.reddit.edit_wiki_page, ctb.conf.reddit.stats.subreddit, page, user_stats, "Update by ALTcointip bot")

    return True
