# Pyside6 Utilities
This repository was created in tandem with [] - it contains several useful PySide6 widgets, models and delegates as well as some utility functions
The package contains registrars for each widget, which can be used register the widgets in QtDesigner to quickly build UI's.


A quick list of the main widgets:
- `CollapsibleGroupBox`
  - A groupbox that acts as a layout, when the user check/unchecks the groupbox, the contents collapse
- `ConsoleWidget`
  - A console-like widget to which multiple files can be mirorred, user can select the items to view the consoleitem-contens
- `DataclassTreeview` (and `DataClassModel` & `DataClassEditorDelegate`)
  - A view/model/delegate combination which mirrors a python dataclass (`@dataclass`) object and provides editors for each of the types defined
- `ExtendedMdiArea` / `FramelessMdiWindow`
  - Based on PySide6.QtWidgets.QMdiArea, provides a way to load custom frameless windows with a custom UI, while also retaining resize/move/etc. operations. 
- `FileExplorerView`
  - Built around the use of a QFileSystemModel - enables right-click operations and undo/redo actions, as well as the possibility to set a "highlighted" file
- `OverlayWidget`
  - Provides a container-widget to which another widget can be provided, when turning the overlay-mode of this widget on, this widget will be overlayed over the contained widget(s). 
- `PandasTableView` (and `PandasTableModel`)
  - Provide an easy way to show and edit pandas dataframes
- `RangeSelector` 
  - Widget to select a range of float/int/datetime etc.  *NOTE: work in progress*


## Installation
The easiest way to install this package is using PyPi
```
pip install **TODO**
```

The package can also be manually installed by downloading this repository, extracting it to the desired install location and installing it using:
```
pip install <path>
```
Optionally, we can provide the `-e` argument to pip to be able to edit the package. 


## Qt-Designer
This package provides registrars for the implemented widgets, meaning that the widgets can be made available directly in qt-designer (only `pyside6-designer` supports this functionality).
To enable this, the environment variable `PYSIDE_DESIGNER_PLUGINS` should be set to `[install_path]/registrars`, so that the widgets can be loaded in using the `QPyDesignerCustomWidgetCollection.registerCustomWidget` method.

Alternatively, this package includes a script which automatically adds this path to `PYSIDE_DESIGNER_PLUGINS` and launches qt-designer. We can run this example by running `<install_path>/examples/run_qt_designer.py` or by importing and running the `run_qt_designer()` using `from pyside6_utilities.examples import run_qt_designer`.

If all is well, this should result in the widgets showing up in the left-hand side of the designer, e.g. for the views:
<img src="./examples/images/Qt_designer_loaded_widgets_example.png" width="400" />
