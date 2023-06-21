"""Implements a single item in a dataclass-tree, representing a variable with its value"""
import typing
from dataclasses import Field


class DataclassTreeItem(object):
	"""
	This class represents a single item in a dataclass-tree (attribute).
	"""
	def __init__(self,
	      		name : str,
				item_data: typing.Any,
				field : Field | None,
				parent: typing.Optional["DataclassTreeItem"] = None
			) -> None:
		self.name = name
		self.item_data = item_data
		self.field = field
		self.parent_item = parent
		self.child_items = []

	def append_child(self, item: "DataclassTreeItem") -> None:
		"""Appends a child to this item (of same type)."""
		self.child_items.append(item)

	def child(self, row: int) -> "DataclassTreeItem":
		"""Returns the child at the given row."""
		return self.child_items[row]

	def child_count(self) -> int:
		"""Returns the number of children."""
		return len(self.child_items)

	def column_count(self) -> int:
		"""Returns the number of columns."""
		return 2

	def data(self) -> typing.Any:
		"""Returns the data stored in this item."""
		return self.item_data

	def get_field(self) -> Field | None:
		"""Returns the field associated with this item."""
		return self.field

	def parent(self) -> "DataclassTreeItem | None":
		"""Returns the parent of this item."""
		return self.parent_item

	def row(self) -> int:
		"""Returns the row of this item."""
		if self.parent_item:
			return self.parent_item.child_items.index(self)
		return 0

	def print(self, indent: int = 0) -> None:
		"""Prints the tree to the console."""
		print("-" * indent, self.item_data)
		for child in self.child_items:
			assert isinstance(child, DataclassTreeItem)
			child.print(indent + 1)
		