#!/usr/bin/python

# First import the various python modules we'll need 
import pywbem
import os
import sys
from optparse import OptionParser

# Dictionary to cache class metadata
classData = {}
def friendlyValue(client, instance, propertyName):
   global classData

   # Start out with a default empty string, in case we don't have a mapping
   mapping = ''

   if instance.classname not in classData:
      # Fetch the class metadata if we don't already have it in the cache
      classData[instance.classname] = client.GetClass(instance.classname, IncludeQualifiers=True)

   myClass = classData[instance.classname]

   # Now scan through the qualifiers to look for ValueMap/Values sets
   qualifiers = myClass.properties[propertyName].qualifiers
   if 'ValueMap' in qualifiers.keys() and 'Values' in qualifiers.keys():
      vals = qualifiers['Values'].value
      valmap = qualifiers['ValueMap'].value
      value = instance[propertyName]
      # Find the matching value and convert to the friendly string
      for i in range(0,len(valmap)-1):
         if str(valmap[i]) == str(value):
             mapping = vals[i]
             break

   return mapping
   

# Display an instance, with 
def printInstance(client, instance):
   #print instance.classname
   healthstate = ''
   elementname = ''
   for propertyName in sorted(instance.keys()):
      if instance[propertyName] is not None:
         if propertyName == 'HealthState':
            healthstate = friendlyValue(client, instance, propertyName)
         if propertyName == 'ElementName':
            elementname = instance[propertyName]
   return (elementname, healthstate)

# Simple function to dump out asset information
def dumpAssetInformation(server, username, password):
   client = pywbem.WBEMConnection('https://'+options.server,
                                  (options.username, options.password),
                                  'root/cimv2')
   list = []
   result_list = []
   for classname in ['CIM_Sensor', 'CIM_PowerSupply']:
      list.extend(client.EnumerateInstances(classname))
   if len(list) == 0:
      print 'Error: Unable to locate any instances'
   else:
      for instance in list:
         result_list.append(printInstance(client, instance))
   return result_list

if __name__ == '__main__':
   # Some command line argument parsing gorp to make the script a little more
   # user friendly.
   usage = '''Usage: %prog [options]

      This program will dump some basic asset information from an ESX host
      specified by the -s option.'''
   parser = OptionParser(usage=usage)
   parser.add_option('-s', '--server', dest='server',
                     help='Specify the server to connect to')
   parser.add_option('-u', '--username', dest='username',
                     help='Username (default is root)')
   parser.add_option('-p', '--password', dest='password',
                     help='Password (default is blank)')
   (options, args) = parser.parse_args()
   if options.server is None:
      print 'You must specify a server to connect to.  Use --help for usage'
      sys.exit(1)
   if options.username is None:
      options.username = 'root'
   if options.password is None:
      options.password = ''

   results = dumpAssetInformation(options.server, options.username, options.password)

   is_ok = True
   resultstate = []
   for elementname, healthstate in results:
      if healthstate != 'OK' and healthstate != '':
         is_ok = False
         resultstate.append('%s: %s' % (healthstate, elementname))
   if is_ok:
      print 'OK: All Hardware is OK'
      sys.exit(0)
   else:
      print 'CRITICAL: %s' % ('\n'.join(resultstate))
      sys.exit(2)
