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
             #mapping = ' ('+vals[i]+')'
             mapping = vals[i]
             break

   return mapping

# Display an instance
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

def getNamespaces(options):
   client = pywbem.WBEMConnection('https://'+options.server,
                                  (options.username, options.password),
                                  'root/interop')
   list = client.EnumerateInstances('CIM_Namespace', PropertyList=['Name'])
   return set(map(lambda x: x['Name'], list))


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
   parser.add_option('-n', '--namespace', dest='namespace', default='root/cimv2',
                     help='Which namespace to access (default is root/cimv2)')
   parser.add_option('-N', '--namspaceonly', dest='namespaceonly', action='store_true',
                     help='Dump the list of namespaces on this system',
                     default=False)
   (options, args) = parser.parse_args()
   if options.server is None:
      print 'You must specify a server to connect to.  Use --help for usage'
      sys.exit(1)
   if options.username is None:
      options.username = 'root'
   if options.password is None:
      options.password = ''

   if options.namespaceonly is True:
      for namespace in getNamespaces(options):
         print '%s' % namespace
      sys.exit(0)

   client = pywbem.WBEMConnection('https://'+options.server,
                                  (options.username, options.password),
                                  options.namespace)

   resultstate = []
   is_ok = True
   for instance in client.EnumerateInstances('CIM_StorageVolume'):
      elementname, healthstate = printInstance(client, instance)
      if healthstate != 'OK':
         is_ok = False
      resultstate.append('%s: %s' % (elementname, healthstate))

   if is_ok:
      print 'OK: %s' % ('\n'.join(resultstate)) 
      sys.exit(0)
   else:
      print 'CRITICAL: %s' % ('\n'.join(resultstate))
      sys.exit(2)
