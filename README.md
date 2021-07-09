# FinalYearProject
This is developed application (User Authentication Web Application with Face Recognition Solution).

In order to steup on your machine, you can follow the steps below:
1. Install the Microsoft IIS with CGI option enabled
    - Click the Windows button on keyboard and type ”Window Features”
    - Select the “Turn Windows Features On or Off”
    - Scroll to “Internet Information Services” and expand the list according to the order: Internet Information Services > World Wide Web Services > Application   Development Features.
    - Then, checked the “Internet Information Services” option and “CGI” option.
    - Click the OK button to install the features.

2. Copy the project’s files to the respective directory
    - Copy webproject to C:/inetpub/wwwroot/webproject

3. Install Python 3.x and install the required Python module
    - Install the Python and check the “Add to PATH” option if available
    - Also, install Development for C++ using Visual Studio Build Tools
    - To install the Python module, open your command prompt and go into C:/inetpub/wwwroot/webproject directory
    - Then, type in the install_requirements.bat file and it will start to install all module requirements for the application and the server.

4. Change the Python file properties
    - Navigate to your installed python file, then edit Properties by right clicking it.
    - Go to the Security tabs, click Edits and Adds button to add the app pool.
    - Then, type “IIS AppPool\DefaultAppPool” and check names and click OK.
    - Also, allow Full control permission for the DefaultAppPool by applying it.

5. Enable the wfastcgi the feature in command prompt
    - Open the command prompt as administrator and go to the root directory (C:\) by type in “cd..”
    - Then, type ”wfastcgi-enable”.
    - Copy the FastCGI script and store it for later steps.

6. Tweak the setting in the project files.
    - Open web-config file inside the root directory of the project with code editor
    - Replace the variable scriptProcessor="<to be filled in>" with the FastCGI script that get from the previous step
    - Rename this file to web.config and move it to the C:/inetpub/wwwroot directory

7. Configure the Microsoft IIS 
    - Go to the server, and click the Configuration Editor.
    - Then, go to the section and find system.webServer/handlers and unlock sections on the right hand side.
    - Go to the Default Web Site under the server and add a virtual directory.
    - Add a virtual directory for the static file and link it to the actual static file directory.
    - Add a virtual directory for the media file and link it to the actual media file directory.
    - Navigate to Application Pools on the left hand side, select DefaultAppPool and right-click to access the advanced setting.
    - Then, go to Identity under Process Model change to “Local System”.

8. Change the settings.py file in the project
    - Open settings.py with code editor.
    - Change the ALLOWED_HOSTS to your local IP address for that machine.
    - Then, open the command prompt with the administrator and change the path to C:/inetpub/wwwroot/webproject directory.
    - Type in “python manage.py collectstatic”
    - Restart the server in the IIS interfaces

9. Open the browser and access that IP address to check whether it is hosted correctly
