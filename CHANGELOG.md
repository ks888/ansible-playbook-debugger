# Changes

## 0.3.0 - Mar 19, 2016

* Support ansible v2, but ansible v1 is not supported anymore
* Simplify commands. see README for more detail

## 0.2.4 - Mar 19, 2016

* Show error message when ansible v2 is used

## 0.2.3 - Apr 25, 2015

* Support assign command. It replaces module_args/complex_args
* Support update command. It partially updates module_args/complex_args
  * `assign/update module_args` accepts key=value pairs format as new module_args
  * `assign/update complex_args` accepts YAML format as new complex_args
  * That is, you can update a module's args using same formats as playbook
* Fix docs so that the difference between module_args and complex_args is clear

## 0.2.2 - Jan 31, 2015

* Support --breakpoint option
* Fix can-not-redo bug on template module
* Fix quit-command-not-actually-quit bug
* Simplify docs and add more examples
* Integrate two hooks to invoke the debugger to one hook so that debugger's behavior is unified.

## 0.2.1 - Jan 17, 2015

* Enable to use [] to access list/dict in print command
* Add --version option
* Connect to travis CI
* Add some documents for developer
* Add more examples

## 0.2.0 - Jan 2, 2015

* Enable to use template in set command (if a playbook has a template error)
* Enable to update the entire module_args in set command
* Improve an error message so that points are clearer
* Add conditions for invoking debugger so that it catches various types of error
* Add more tests
* Various bugfixes

## 0.1.0 - Dec 24, 2014

* Initial release
