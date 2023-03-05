# Pyside6 Widgets
This repository contains some additional widgets and registrars, which can be used to enable the use of these widgets in QtDesigner. 

A list of the widgets:


- CollapsibleGroupBox
  - A groupbox that acts as a layout, when the user check/unchecks the groupbox, the contents collapse
- 








## Use with QT Designer
We can test whether all widgets are working as intended by running:
```
python ./run_qt_designer.py
```

If you want to use these widgets inside of Qt Designer, the environment variable `PYSIDE_DESIGNER_PLUGINS` should be set to the path of `[install_path]/Registrars`. 

## Qt For Python & Visual Studio Code
The extensions **Qt for Pyton** can be used to edit `.ui` files in VSCode, to automatically add these widgets to the editor, go to the extension settings, then:
```
Qt For Python > Designer:Options
```
Then click on ``add``, then point to `[install_path]/Registrars`.
E.g.:
