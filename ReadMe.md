# ReadMe

albion-discordbot is a project created for personal use. The main use of this bot is the same as any other Albion Online discord Killbot.

At the moment, only the Killbot function of the bot is added, and some visual in the generated images are off. 

If you'd like to have this running yourself. You'll only need to create a config.json file as per config_sample.json. Everything else can be directly run.

## Config File.

I use a personal [Cloudinary](https://cloudinary.com/) free account to store saved images. For this reason, the config file also requires you to enter Cloudinary details. Images stored on cloudinary are the final version of the kill-death image, and the victim's inventory. If the current running version of the bot uploads a total of 20 images (number can be changed), the same 20 images would be deleted, to minimize redundant space usage.

Discord Token is to be taken from the discord bot creation menu. 

Discord Channel is required as I've kept it static, to message on only one channel. You can get this value by right clicking on a channel and selecting "Copy ID".

albion_alliances, albion_guilds and albion_players are string lists. It is not case sensitive.


## Sample Message Commands.
I've added two sample commands to ensure that the bot works.

```
$kb_sample
```
This command would retrieve the first kill-death information available from the api.

```
$kb_sample_debug
```
In addition to the command above, this command will also print to console, the list of extracted information. This can be used to help add/edit/remove extracted data from the api.

--

No other messages would be recognized.


## Heroku

There's a worker Procfile within this repository. Therefore you can directly deploy the application on Heroku.

Be sure to enable the worker dyno under the resource tab.

## Storage
Image generations are done locally, then uploaded onto Cloudinary. Additionally, items that need to be added onto an image is also downloaded to the local folder.

There's a portion of the script that would delete the locally downloaded images to save storage space.
