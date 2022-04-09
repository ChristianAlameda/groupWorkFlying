How to use:
Write a script in telloController.py to control the movements of the tello.

telloController.py already contains some sample movements:

	t = tello.Tello()
	try:
		start_battery = t.get_battery()
		print("Battery percentage: %s" % start_battery)
		t.takeoff()
		time.sleep(0.5)
		t.move_up(100)
		t.flip("f")
		t.flip("b")
		t.rotate_cw(180)
	except Exception as e:
		log.error(e)
	t.land()
	end_battery = t.get_battery()
	print("Battery percentage: %s" % end_battery)
	print("Battery used for flight %s" % (start_battery - end_battery))

This equivalent to:

	display battery percentage,
	take off,
	wait for half a second,
	move up 100 cm,
	flip forward,
	flip backwards,
	rotate clockwise 180 degrees,
	land,
	display battery percentage,
	display battery percentage used during the flight


Once you've written your command script, power on the tello and connect to the wi-fi 
network produced by the tello.  Run telloController.py, and the tello should follow 
your script.

Furthermore, once you understand how telloController.py and tello.py work, you can even 
implement your own abstract movements based on the ones provided as is already done in 
the fly_poly function.