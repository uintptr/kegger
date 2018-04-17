# Scripts

* `sample.py`
    * Trying to troubleshoot a problem with either the HX711 chip or the load cells. Weight isn't very stable across time and it seems to be creeping upwards

* `startup.sh`
    * To be added to the user's cronjob so the server starts after rebooting

    ```
    crontab -e

    @reboot $HOME/kegger/scripts/startup.sh
    ```

* `xsession`
    * Xorg session configuration file so the UI starts automatically

    ```
    ln -s $HOME/kegger/scripts/xsession ~/.xsession
    ```
