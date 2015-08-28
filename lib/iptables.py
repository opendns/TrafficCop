#!/usr/bin/env python
"""
library to interact with iptables
to support TrafficCop tool
"""

import subprocess
from subprocess import Popen, PIPE
import sys


class Iptables:

    @staticmethod
    def getCurrentRuleset():
        """retrieves current iptables ruleset"""

        cmd = "sudo /sbin/iptables-save"
        return subprocess.check_output(cmd.split(" "))

    @staticmethod
    def loadNewRuleset(ruleset):
        """loads modified iptables ruleset"""

        cmd = "sudo /sbin/iptables-restore"
        p = Popen(cmd.split(" "), stdin=PIPE)
        p.communicate(input=ruleset)
        #return subprocess.check_call(cmd.split(" "), stdin=ruleset)
        p.wait()
        return p.returncode

    @staticmethod
    def hasExistingRules(rules, chain):
        """checks if chain has existing rules or not"""
        for rule in rules:
            if ("-A " + chain) in rule:
                return True
        return False

    @staticmethod
    def getRules(ruleset):
        """grabs all rules from the ruleset"""
        rules = []
        for line in ruleset.split('\n'):
            if ("-A ") in line:
                rules.append(line)
        return rules

    @staticmethod
    def modifyRuleset(ruleset):
        """modifies exported iptables ruleset to add logging chains
        in preparation for TrafficCop analysis
        """

        newRuleset = []

        # check if already configured for TrafficCop
        if 'LOG_ACCEPT_INPUT' in ruleset or\
           'LOG_DROP_INPUT' in ruleset or\
           'LOG_ACCEPT_OUTPUT' in ruleset or\
           'LOG_DROP_OUTPUT' in ruleset:
            print "It appears you're already configured for TrafficCop logging!"
            print "Please reset your iptables configuration if you want to start fresh"
            print "(tcop clear && tcop enable)"
            print "quitting..."
            sys.exit(1)

        currentRules = Iptables.getRules(ruleset)

        newRules = []

        # add log_accept/drop rules if chains are empty
        if not Iptables.hasExistingRules(rules=currentRules, chain="INPUT"):
            newRules.append("-A INPUT -j LOG_ACCEPT_INPUT")
        if not Iptables.hasExistingRules(rules=currentRules, chain="OUTPUT"):
            newRules.append("-A OUTPUT -j LOG_ACCEPT_OUTPUT")

        # redirect existing ACCEPT/DROP rules to new chains which add logging
        for rule in currentRules:
            if '-A INPUT' in rule:
                rule = rule.replace('-j ACCEPT', '-j LOG_ACCEPT_INPUT')
                rule = rule.replace('-j DROP', '-j LOG_DROP_INPUT')
                newRules.append(rule)

            elif '-A OUTPUT' in rule:
                rule = rule.replace('-j ACCEPT', '-j LOG_ACCEPT_OUTPUT')
                rule = rule.replace('-j DROP', '-j LOG_DROP_OUTPUT')
                newRules.append(rule)

        filterSectionHit = False
        rulesAdded = False
        for line in ruleset.split('\n'):
            # add new logging chains to filter
            if '*filter' in line:
                filterSectionHit = True

                # leave the filter header alone
                newRuleset.append(line)

                # but add new log chains
                newRuleset.append(':LOG_ACCEPT_INPUT - [0:0]')
                newRuleset.append(':LOG_ACCEPT_OUTPUT - [0:0]')
                newRuleset.append(':LOG_DROP_INPUT - [0:0]')
                newRuleset.append(':LOG_DROP_OUTPUT - [0:0]')

                # add rules to those log chains
                newRules.append('-A LOG_ACCEPT_INPUT -p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j NFLOG --nflog-prefix "CHAIN=INPUT ACTION=ACCEPT"')
                newRules.append('-A LOG_ACCEPT_INPUT -j ACCEPT')

                newRules.append('-A LOG_ACCEPT_OUTPUT -p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j NFLOG --nflog-prefix "CHAIN=OUTPUT ACTION=ACCEPT"')
                newRules.append('-A LOG_ACCEPT_OUTPUT -j ACCEPT')

                newRules.append('-A LOG_DROP_OUTPUT -p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j NFLOG --nflog-prefix "CHAIN=OUTPUT ACTION=DENY"')
                newRules.append('-A LOG_DROP_OUTPUT -j DROP')

                newRules.append('-A LOG_DROP_INPUT -p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j NFLOG --nflog-prefix "CHAIN=INPUT ACTION=DROP"')
                newRules.append('-A LOG_DROP_INPUT -j DROP')

            # remove existing rule lines (we'll add them back later)
            elif '-A ' in line:
                pass

            # rules go right before COMMIT line
            elif 'COMMIT' in line:
                # we only want to add the new rules in the filter section
                if filterSectionHit and not rulesAdded:
                    newRuleset += newRules
                    rulesAdded = True

                # always add the COMMIT line back in
                newRuleset.append(line)

            # default is to leave all other lines alone
            else:
                newRuleset.append(line)

        newRulesetString = ''
        for line in newRuleset:
            newRulesetString += line + '\n'

        return newRulesetString.strip()

    @staticmethod
    def clearAllRules():
        try:
            cmds = ['sudo iptables -P INPUT ACCEPT',
                    'sudo iptables -P FORWARD ACCEPT',
                    'sudo iptables -P OUTPUT ACCEPT',
                    'sudo iptables -t nat -F',
                    'sudo iptables -t mangle -F',
                    'sudo iptables -F',
                    'sudo iptables -X',
                    ]
            for cmd in cmds:
                subprocess.check_output(cmd.split(" "))
            return 0
        except:
            return 1
