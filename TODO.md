* Refactorings
    * Move preprocessing out of RescueTime class into an iteration-based pipeline
    * Generalise modules into functions, not classes
        * Rescuetime
        * GcalSyncer

* Timezone support

* Remove use of pandas, instead use dataclasses

* More granular information support
    * Window title support
        * Can this be done with the rescuetime API?
            * Does not look like it
        * May require switching providers
            * Requirements
                * Sync
            * Candidates
                * ActivityWatch 
                    * Open source
                    * Tons of extensions
                    * Sync appears unstable

    * Which projects are open in VSCode
        * Can use Wakatime

    * Or the title of the document I have worked on in Word/Obsidian

* CLI
    * Get credentials from environment variables 
    * Remove credentials from
        * Git repo (credentials folder)
        * main.py (API_KEY)
