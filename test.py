#!/usr/bin/env python

# Imports
import dbus
import time
import os
import sys
import datetime
import logging


# Victron Imports
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
from vedbus import VeDbusItemImport
from vedbus import VeDbusItemExport


class CCGXController(object):

	def __init__(self):

		self.bus = dbus.SystemBus()
		self.DbusServices = {
	  
			'CCGXRelay': {'Service': "com.victronenergy.system",
						   'Path': "/Relay/0/State",
						   'Value': 0},
			'L1Power': {'Service': "com.victronenergy.system",
						'Path': "/Ac/Grid/L1/Power",
						'Value': 0},
			'L2Power': {'Service': "com.victronenergy.system",
						'Path': "/Ac/Grid/L2/Power",
						'Value': 0},
			'L3Power': {'Service': "com.victronenergy.system",
						'Path': "/Ac/Grid/L3/Power",
						'Value': 0}    
			}

		self.Settings = {
   
			'MinInPower': -50,
			'MaxInPower': 500,
			'Duration': datetime.timedelta(minutes = 1),
			'Test1': False,
			'Done': False,
			'StartTime':datetime.datetime.now().time(),
			'ActiveTime': datetime.time(hour=10, minute=8),
			'Endtime':datetime.datetime.now().time()
			}

	def Throttle(self):
		if self.Settings['Test1']==False:
			self.setrelay(0)

		if self.Settings['Test1']==True:

		   if self.Settings['Done']== False:
			  self.Settings['StartTime']=datetime.datetime.now().time()
			  self.Settings['Endtime']=(datetime.datetime.combine(datetime.date.today(), self.Settings['StartTime']) +self.Settings['Duration']).time()

		   if datetime.datetime.now().time() <= self.Settings['Endtime'] and self.Settings['Test1']==True:
				 self.setrelay(1)
				 self.Settings['Done']=True
		   if datetime.datetime.now().time() >= self.Settings['Endtime'] and self.Settings['Done']==True:
				self.setrelay(0)
	

	def getvalues(self):

		for service in self.DbusServices:
			try:
				self.DbusServices[service]['Value'] = VeDbusItemImport(
						bus=self.bus,
						serviceName=self.DbusServices[service]['Service'],
						path=self.DbusServices[service]['Path'],
						eventCallback=None,
						createsignal=False).get_value()
				# print 'New value of ', self.DbusServices[service]['Value'], 'for', service
			except dbus.DBusException:
				print 'Error with DBus'
				print service

			try:
				self.DbusServices[service]['Value'] *= 1
				self.DbusServices[service]['Value'] = max(self.DbusServices[service]['Value'], -5000)
			except:
				if service == 'L1Power' or service == 'L2Power' or service == 'L3Power':
					self.DbusServices[service]['Value'] = 0
					# print 'No value on:', service         	
	

	def setrelay(self, relayvalue):

		VeDbusItemImport(
			bus=self.bus,
			serviceName=self.DbusServices['CCGXRelay']['Service'],
			path=self.DbusServices['CCGXRelay']['Path'],
			eventCallback=None,
			createsignal=False).set_value(relayvalue)


	def run(self):

		# Initialize elements of the main loop
		print 'Main loop started'
  
		self.setrelay(0)
		
		while True:
			 self.getvalues()
			 L1Out = self.DbusServices['L1Power']['Value']
			 L1Out = max(L1Out,-5000)
			 L2Out = self.DbusServices['L2Power']['Value']
			 L2Out = max(L2Out,-5000)
			 L3Out = self.DbusServices['L3Power']['Value']
			 L3Out = max(L3Out,-5000)
			 OutPower = L1Out + L2Out + L3Out
			
			 if L1Out <= self.Settings['MinInPower'] or L2Out <= self.Settings['MinInPower'] or L3Out <= self.Settings['MinInPower'] :
				self.Settings['Test1'] =True
			 if L1Out >= self.Settings['MaxInPower'] or L2Out>= self.Settings['MaxInPower'] or L3Out>= self.Settings['MaxInPower']:
				self.Settings['Test1'] =False
				self.Settings['Done']= False

			 self.Throttle()
		  



if __name__ == "__main__":
	controller = CCGXController()
	controller.run()