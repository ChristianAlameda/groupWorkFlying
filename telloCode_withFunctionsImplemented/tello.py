import socket
import threading
import time
import traceback

class Tello:
	"""Wrapper to simply interactions with the Ryze Tello drone."""

	def __init__(self, units="cm", local_ip="", local_port=8888, interface_name="no-interface", command_timeout=10.0, tello_ip="192.168.10.1", tello_port=8889):
		"""Binds to the local IP/port and puts the Tello into command mode.

		Args:
			units (str): Units to use for movement, "cm", "in", "m", "ft".
			local_ip (str): Local IP address to bind.
			local_port (int): Local port to bind.
			command_timeout (int|float): Number of seconds to wait for a response to a command.
			tello_ip (str): Tello IP.
			tello_port (int): Tello port.

		Raises:
			RuntimeError: If the Tello rejects the attempt to enter command mode.

		"""
		if units == "cm" or units == "in" or units == "m" or units == "ft":	
			self.units = units
		else:
			raise RuntimeError("Incorrect units, must use 'cm', 'in', 'm', or 'ft' ")
		
		self.abort_flag = False
		self.command_timeout = command_timeout
		self.response = None
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		self.socket.bind((local_ip, local_port))
		
		if interface_name != "no-interface":
			self.socket.setsockopt(socket.SOL_SOCKET, 25, interface_name.encode(encoding="utf-8"))
		self.tello_address = (tello_ip, tello_port)

		self.receive_thread = threading.Thread(target=self._receive_thread)
		self.receive_thread.daemon=True

		self.receive_thread.start()

		if self.send_command("command") != "ok":
			raise RuntimeError("Tello rejected attempt to enter command mode")

	def __del__(self):
		"""Closes the local socket."""

		self.socket.close()
		
	def send_command(self, command):
		"""Sends a command to the Tello and waits for a response.

		If self.command_timeout is exceeded before a response is received,
		a RuntimeError exception is raised.

		Args:
			command (str): Command to send.

		Returns:
			str: Response from Tello.

		Raises:
			RuntimeError: If no response is received within self.timeout seconds.
		"""

		self.abort_flag = False
		timer = threading.Timer(self.command_timeout, self.set_abort_flag)

		self.socket.sendto(command.encode(encoding="utf-8"), 0, self.tello_address)

		timer.start()

		while self.response is None:
			if self.abort_flag is True:
				raise RuntimeError("No response to command")

		timer.cancel()

		response = self.response.decode(encoding="utf-8")
		self.response = None

		return response

	def set_abort_flag(self):
		"""Sets self.abort_flag to True.

		Used by the timer in Tello.send_command() to indicate that a response
		timeout has occurred.

		"""

		self.abort_flag = True

	def _receive_thread(self):
		"""Listens for responses from the Tello.

		Runs as a thread, sets self.response to whatever the Tello last returned.

		"""
		while True:
			try:
				self.response, ip = self.socket.recvfrom(1518)
			except Exception:
				break

	def flip(self, direction):
		"""Flips in a direction.

		Args:
			direction (str): Direction to flip, "l", "r", "f", "b", "lb", "lf", "rb" or "rf".

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		return self.send_command("flip %s" % direction)

	def get_battery(self):
		"""Gets percent battery remaining.

		Returns:
			int: Percent battery remaining.

		"""

		battery = self.send_command("battery?")

		try:
			battery = int(battery)
		except:
			pass

		return battery

	def get_flight_time(self):
		"""Returns the number of seconds elapsed during flight.

		Returns:
			int: Seconds elapsed during flight.

		"""

		flight_time = self.send_command("time?")

		try:
			flight_time = int(flight_time)
		except:
			pass

		return flight_time

	def get_speed(self):
		"""Returns the current speed.

		Returns:
			int: Current speed.

		"""

		speed = self.send_command("speed?")

		try:
			speed = float(speed)

			if self.units == "in":
				speed = round((speed * 2.54), 1)
			elif self.units == "m":
				speed = round((speed * 100), 1)
			elif self.units == "ft":
				speed = round((speed * 2.54 * 12), 1)
		except:
			pass

		return speed
		
	def set_speed(self, speed):
		"""Sets speed.

		This method expects MPS. The Tello API expects speeds from
		1 to 100 centimeters/second.

		0.01 to 1 MPS

		Args:
			speed (int|float): Speed.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		speed = float(speed)

		if self.units == "in":
			speed = round((speed * 2.54), 1)
		elif self.units == "m":
			speed = round((speed * 100), 1)
		elif self.units == "ft":
			speed = round((speed * 2.54 * 12), 1)
				
		if speed < 1 or speed > 100:
			raise RuntimeError("Requested speed is out of bounds 0.01 - 1 (%s)" % speed)

		return self.send_command("speed %s" % speed)

	def takeoff(self):
		"""Initiates take-off.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""
		
		print("Taking off")
		return self.send_command("takeoff")

	def land(self):
		"""Initiates landing.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		return self.send_command("land")

	def move(self, direction, distance):
		"""Moves in a direction for a distance.

		This method expects meters. The Tello API expects distances
		from 20 to 500 centimeters.

		0.2 to 5 meters

		Args:
			direction (str): Direction to move, "forward", "back", "right", "left", "up", or "down".
			distance (int|float): Distance to move.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		distance = float(distance)
		
		if self.units == "in":
			distance = round(distance * 2.54)
		elif self.units == "m":
			distance = round(distance * 100)
		elif self.units == "ft":
			distance = round(distance * 2.54 * 12)
		
		if distance < 20 or distance > 500:
			raise RuntimeError("Requested distance is out of bounds 0.2 - 5 (%s)" % distance)

		if direction != "forward" and direction != "back" and direction != "left" and direction != "right" and direction != "up" and direction != "down":
			raise RuntimeError("%s is not a valid direction" % direction)

		print("Moving %s, %s cm" % (direction, distance))
		return self.send_command("%s %s" % (direction, distance))

	def move_backward(self, distance):
		"""Moves backward for a distance.

		See comments for Tello.move().

		Args:
		distance (int): Distance to move.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		return self.move("back", distance)

	def move_down(self, distance):
		"""Moves down for a distance.

		See comments for Tello.move().

		Args:
			distance (int): Distance to move.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""

		return self.move("down", distance)

	def move_forward(self, distance):
		"""Moves forward for a distance.

		See comments for Tello.move().

		Args:
			distance (int): Distance to move.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""
		return self.move("forward", distance)

	def move_left(self, distance):
		"""Moves left for a distance.

		See comments for Tello.move().

		Args:
			distance (int): Distance to move.

		Returns:
			str: Response from Tello, "ok" or "false".

		"""
		return self.move("left", distance)

	def move_right(self, distance):
		"""Moves right for a distance.

		See comments for Tello.move().

		Args:
			distance (int): Distance to move.
		
		Returns:
			str: Response from Tello, "ok" or "false".

		"""
		return self.move("right", distance)

	def move_up(self, distance):
		"""Moves up for a distance.

		See comments for Tello.move().

		Args:
			distance (int): Distance to move.

		Returns:
		str: Response from Tello, "ok" or "false".

		"""

		return self.move("up", distance)

	def rotate(self, direction, degrees):
		"""Rotates clockwise or couter-clockwise.

		Args:
			direction (str): Direction to spin, "cw" or "ccw".
			degrees (int): Degrees to rotate, 1 to 360.

		Returns:
			str: Response from Tello, "ok" or "false".
			
		Raises:
			RuntimeError: If direction is not a valid direction.
			RuntimeError: If degrees is not in the range 1 to 360

		"""

		if degrees < 1 or degrees > 360:
			raise RuntimeError("Requested rotation degrees is out of bounds 1 - 360 (%s)" % degrees)
        
		if direction == "cw":
			print("Rotating %s %s degrees" % (direction, degrees))
			return self.send_command("cw %s" % degrees)
		elif direction == "ccw":
			print("Rotating %s %s degrees" % (direction, degrees))
			return self.send_command("cww %s" % degrees)
		else:
			raise RuntimeError("%s is not a valid rotation direction" % direction)
			
	def rotate_cw(self, degrees):
		"""Rotates clockwise a given number of degrees
		
		Args:
			degrees (int): Degrees to rotate, 1 to 360.
			
		Returns:
			str: response from Tello, "ok" or "false".
		
		"""
		
		return self.rotate("cw", degrees)
	
	def rotate_ccw(self, degrees):
		"""Rotates counter-clockwiseclockwise a given number of degrees
		
		Args:
			degrees (int): Degrees to rotate, 1 to 360.
			
		Returns:
			str: response from Tello, "ok" or "false".
		
		"""
		
		return self.rotate("ccw", degrees)
	
	def spin(self, direction, rotations):
		"""Spins clockwise or counter-clockwise.
		
		Args:
			direction (str): Direction to spin, "cw" or "ccw".
			rotations (int): Number of times to spin.
			
		Returns:
			str: Response from Tello, "ok" or "false".
			
		Raises: 
			RuntimeError: If direction is not a valid direction.
			
		"""
	
		if direction == "cw":
			print("Spinning cw %s times" % rotations)
			for i in range(rotations):
				response = self.send_command("cw 360")
			return response
		elif direction == "ccw":
			print("Spinning ccw %s times" % rotations)
			for i in range(rotations):
				response = self.send_command("ccw 360")
			return response
		else:
			raise RuntimeError("%s is not a valid rotation direction" % direction)
			
	def fly_poly(self, sides, distance):
		"""Flys around the perimeter of a polygon
		
		Args:
			sides (int): The number of sides of the polygon
			distance (int): The length of each side of the polygon (Restricted by move())
	
		"""
		
		print("Beginning polygon flight, flying %s sides at %s cm per side" % (sides, distance))
		for s in range(sides):
			self.move_forward(distance)
			time.sleep(0.1)
			self.rotate('cw', round(360/sides))
			time.sleep(0.1)