"""
Helper class to serialize and deserialize objects
for now, only json is supported, but more formats can be added. 
"""
import json

class Serializable():
	"""Generic class to serialize and deserialize objects to/from files"""
	def to_file(self, path : str, filetype = "json", ignore_private = False, use_encoding="utf-8"):
		"""Trioes to find the correct function to save this object to a file, then saves it to the passed path

		Args:
			path (str): The path to save the file to
			filetype (str, optional): What filetype to save to. Defaults to "json".
			ignore_private (bool, optional): Whether to ignore private attributes. Defaults to True.
			use_encoding (str, optional): What encoding to use. Defaults to "utf-8".

		Raises:
			NotImplementedError: _description_
		"""
		func = getattr(self, "to_"+filetype)
		if func is None:
			raise NotImplementedError(f"Could not save to passed filetype ({filetype}), this filetype is not implemented")
		else:
			output = func(ignore_private=ignore_private)
			with open(path, "w", encoding=use_encoding) as file:
				file.write(output)

	def from_file(self, path : str, filetype = "json", use_encoding="utf-8"):
		"""
		Load this class from a file
		Args:
			path (str): The path to load the file from
			filetype (str, optional): What filetype to load from. Defaults to "json".
			use_encoding (str, optional): What encoding to use - if applicable. Defaults to "utf-8".
		"""
		# if filetype == "json":
		# 	with open(path, "w") as file:
		# 		file.write(self.tojson())

		func = getattr(self, "from_"+filetype)

		if func is None or filetype == "to_":
			raise NotImplementedError(f"Could not save to passed filetype ({filetype}), this filetype is not implemented")
		else:
			with open(path, "r", encoding=use_encoding) as file:
				func(file.read())

		# self.copy_from_dict(dict)


	def copy_from_dict(self, copy_from_dict : dict, ignore_new_attributes = False):
		""" Copies all attributes from a dict to this object

		Args:
			copy_from_dict (dict): Dictionary to copy from
			ignore_new_attributes (bool, optional): If True, will ignore attributes that are not already present in this
				object. Defaults to False.

		Returns:
			list: list of items that were in the copy dict, but no attribute of this object
			list: list of items that were in this item, but not in the copy dict
		"""
		problem_list = set([])
		if ignore_new_attributes:
			for key in copy_from_dict:
				if not hasattr(self, key):
					problem_list.add(key)

		for key in copy_from_dict:
			if ignore_new_attributes and key in problem_list:
				continue
			setattr(self, key, copy_from_dict[key])

		missing_keys = set([key for key in self.__dict__ if key not in copy_from_dict])

		return list(problem_list), list(missing_keys) #Return list of attributes that were not set


	def to_json(self, ignore_private = False):
		"""Returns a json string representation of this object when converted to a dict"""
		if ignore_private:
			raise NotImplementedError("Ignore-private json conversion not implemented yet")
		return json.dumps(self, default=lambda o: o.__dict__,
			sort_keys=True, indent=4)

	def from_json(self, json_string):
		"""Loads this object from a json string - all attributes present in the json string will be set on this object"""
		load_dict = json.loads(json_string)
		for key in load_dict:
			setattr(self, key, load_dict[key]) #Try to set all attributes from json
