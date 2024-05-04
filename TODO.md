* Refactorings
    * Move preprocessing out of RescueTime class into an iteration-based pipeline
    * Generalise modules into functions, not classes
        * Rescuetime
        * GcalSyncer

* Timezone support

* Remove use of pandas, instead use dataclasses

* Window title support
    * E.g. which projects is open in VSCode
    * Can this be done with the rescuetime API?
    * May require switching providers

* CLI
    * Get credentials from environment variables 
