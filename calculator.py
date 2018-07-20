import pandas as pd
from numbers import Number
import argparse
import sys

aircraft = pd.read_csv('aircraft.csv')
arms = pd.read_csv('arms.csv')
instructors = pd.read_csv('instructors.csv')
restrictions = pd.read_csv('restrictions.csv')

#get instructor name, returns weight
def get_inst_weight():
	
	prompt = 'Enter instructor code: '
	
	while True:
		code = raw_input(prompt)
		if not instructors[instructors.Code == code].empty:
			return float(instructors[instructors.Code == code].iloc[0]['Weight'])
		else:
			print('Code not found')
			continue
#get student weight
def get_stud_weight(num):
	
	prompt = 'Enter student ' + str(num) + ' weight in pounds: '
	
	while True:
		weight = raw_input(prompt) 
		try:
			if isinstance(float(weight), Number) and float(weight) >= 0:
				return float(weight)
			else:
				print('student weight cannot be less than zero')
				continue
		except:
			print('Invalid weight')
			continue
#get fuel load in pounds
def get_trip_fuel():
	
	max_fuel_weight = float(restrictions[restrictions.Description == 'Max Fuel'].iloc[0]['Quantity'])
	prompt = 'Enter fuel load in pounds or \'max\' for full 240 lbs: '
	
	while True:
		fuel_load = raw_input(prompt)
		if fuel_load == 'max':
			return max_fuel_weight - 6
			break
		else:
			try:
				if isinstance(float(fuel_load),Number) and  max_fuel_weight >= float(fuel_load) > 0 :
					return float(fuel_load) - 6
					break
				else:
					print('Fuel load exceeds max of: ' + str(max_fuel_weight) + ' lbs or is less than or equal to 0')
					continue
			except:
				print('invalid fuel load')
				continue
#get baggage load in pounds:
def bags(pos):
	
	max_bags = float(restrictions[restrictions.Description == pos].iloc[0]['Quantity'])
	prompt = 'Enter ' + pos + ' baggage weight in pounds: '
	
	while True:
		bag_weight = raw_input(prompt)
		try: 
			if isinstance(float(bag_weight),Number) and max_bags >= float(bag_weight) >= 0:
				return float(bag_weight)
			else:
				print('baggage too heavy, or negative weight entered ')
				continue
		except:
			print('Invalid weight')
			continue
#get estimated fuel burn 11 gal/h 6 lbs/gal
def fuel_burn_weight():
	prompt = 'Enter flight time in hours: '
	while True:
		flight_time = raw_input(prompt)
		max_usable_fuel = float(restrictions[restrictions.Description == 'Max Usable Fuel'].iloc[0]['Quantity'])
		fuel_density = float(restrictions[restrictions.Description == 'Density of 100LL'].iloc[0]['Quantity'])
		fuel_rate = float(restrictions[restrictions.Description == 'Fuel Burn Rate'].iloc[0]['Quantity'])

		try:
			if isinstance(float(flight_time),Number) and float(flight_time) > 0:
				fuel_burn_weight = float(flight_time)*fuel_rate*fuel_density
				if fuel_burn_weight <= max_usable_fuel*fuel_density*fuel_rate:
					return fuel_burn_weight
				else:
					print ('Fuel burn exceeds max usable fuel')
					continue
			else:
				print('Flight time cannot be negative or zero')
				continue
		except:
			print('Invalid flught time')
			continue
#perform weight and return list of aircraft, assumes 6 lbs taxi fuel 
def weight(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube):

	output_list = pd.DataFrame()
	output_cols = ['Registration','Shaded','MTOW','TOW','MTOW - TOW']

	shaded_mtow = float(restrictions[restrictions.Description == 'MZFW/MTOW shaded'].iloc[0]['Quantity'])
	mtow = float(restrictions[restrictions.Description == 'MZFW/MTOW'].iloc[0]['Quantity'])

	load = instructor_weight + student_1 + student_2 + trip_fuel + baggage_compartment + baggage_tube

	for index, row in aircraft.iterrows():
		tow = load + float(row.BEW)
		if row.Shaded == 'N' and mtow >= tow:
			output_list = output_list.append(pd.DataFrame([(row.Aircraft,row.Shaded,mtow,tow,mtow-tow)] ,columns=output_cols),ignore_index=True)
		if row.Shaded == 'Y' and shaded_mtow >= tow:
			output_list = output_list.append(pd.DataFrame([(row.Aircraft,row.Shaded,shaded_mtow,tow,shaded_mtow-tow)] ,columns=output_cols),ignore_index=True)
	
	return output_list
#calculate CG
def cg(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube,fuel_burn):

	output_list = pd.DataFrame()
	output_cols = ['Registration','Takeoff CG','Aft TOCG Difference', 'Forward TOCG Difference', 'Landing CG','Aft TOCG Difference', 'Forward TOCG Difference']

	front_moment = arms[arms.Label == 'Front Pax'].iloc[0]['Arm'] * (instructor_weight+student_1)
	aft_pax_moment =  arms[arms.Label == 'Aft Pax'].iloc[0]['Arm'] * student_2
	baggage_compartment_moment = arms[arms.Label == 'Baggage Compartment'].iloc[0]['Arm']*baggage_compartment 
	baggage_tube_moment =  arms[arms.Label == 'Baggage Tube'].iloc[0]['Arm'] * baggage_tube 
	takeoff_fuel_moment = arms[arms.Label == 'Fuel'].iloc[0]['Arm'] * trip_fuel 
	landing_fuel_moment = arms[arms.Label == 'Fuel'].iloc[0]['Arm'] * (trip_fuel-fuel_burn)

	load = instructor_weight + student_1 + student_2 + trip_fuel + baggage_compartment + baggage_tube

	aft_cg_limit = float(restrictions[restrictions.Description == 'Aft CG Limit'].iloc[0]['Quantity'])

	for index,row in aircraft.iterrows():
		empty_moment =  row.Moment
		tow = load + float(row.BEW)
		tow_moment = front_moment + aft_pax_moment + baggage_compartment_moment + baggage_tube_moment + takeoff_fuel_moment + empty_moment
		ldgw = tow - fuel_burn
		ldg_moment = front_moment + aft_pax_moment + baggage_compartment_moment + baggage_tube_moment + landing_fuel_moment + empty_moment
		tow_CG = tow_moment/tow
		ldg_CG = ldg_moment/ldgw

		forward_cg_limit_tow = forward_cg(tow)
		forward_cg_limit_ldgw = forward_cg(ldgw)
		
		if forward_cg_limit_tow <= tow_CG <= aft_cg_limit and forward_cg_limit_ldgw <= ldg_CG <= aft_cg_limit:
			output_list = output_list.append(pd.DataFrame([(row.Aircraft, tow_CG, aft_cg_limit-tow_CG, tow_CG-forward_cg_limit_tow, ldg_CG, aft_cg_limit-ldg_CG, ldg_CG-forward_cg_limit_ldgw)] ,columns=output_cols),ignore_index=True)

	return output_list

#calculates forward CG limit, function of total weight
def forward_cg(weight):

	forward_cg_min = float(restrictions[restrictions.Description == 'Forward CG Limit Min'].iloc[0]['Quantity'])
	forward_cg_mtow = float(restrictions[restrictions.Description == 'Forward CG Limit MTOW'].iloc[0]['Quantity'])
	forward_cg_mtow_shaded = float(restrictions[restrictions.Description == 'Forward CG Limit MTOW Shaded'].iloc[0]['Quantity'])

	aft_cg_limit = float(restrictions[restrictions.Description == 'Aft CG Limit'].iloc[0]['Quantity'])

	shaded_mtow = float(restrictions[restrictions.Description == 'MZFW/MTOW shaded'].iloc[0]['Quantity'])
	mtow = float(restrictions[restrictions.Description == 'MZFW/MTOW'].iloc[0]['Quantity'])
	#magic number
	lower_limit = 2161

	#3 regimes
	
	#regime 1: shaded aircraft between 2646 lbs and mtow 2535 lbs
	slope_1 = (forward_cg_mtow_shaded - forward_cg_mtow)/(shaded_mtow - mtow)
	if shaded_mtow >= weight > mtow:
		return forward_cg_mtow_shaded - slope_1*(shaded_mtow-weight)

	#regime 2: between 2535 lbs and 2161 lbs
	slope_2 = (forward_cg_mtow - forward_cg_min)/(mtow - lower_limit)
	if mtow >= weight > lower_limit:
		return forward_cg_mtow - slope_2*(mtow-weight)
	
	#regime 3: less than 2161 lbs
	if weight <= lower_limit:
		return forward_cg_min
#Find Aircraft within MTOW, if mode is weight, just weight calc, if mode cg, then both.
def find_Aircraft():
	instructor_weight = get_inst_weight()
	student_1 = get_stud_weight(1)
	student_2 = get_stud_weight(2)
	trip_fuel = get_trip_fuel()
	baggage_compartment = bags('Baggage Compartment')
	baggage_tube = bags('Baggage Tube')
	fuel_burn = fuel_burn_weight()
	# if mode == 'weight':
	# 	weight(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube)
	# if mode == 'cg':
	# 	cg(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube,fuel_burn)

	weight_list = weight(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube)
	cg_list = cg(instructor_weight,student_1,student_2,trip_fuel,baggage_compartment,baggage_tube,fuel_burn)

	merge = weight_list.merge(cg_list, how = 'inner', on = 'Registration')

	print merge

# find_Aircraft('weight')
find_Aircraft()