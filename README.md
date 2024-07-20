<h2>Area-Analyser</h2>
This is a python 3.9 script which takes a file.png or folder of .png and breaks down the images into a set size. 
For example a 10000x10000px satellite image with the target size set to 250x250px, you will get 1600 small pictures as a result.

But the img-breakdown is only part 1.
The output of imgs is optional. The script also analyses each new image and calculates a percentage of a color in the images. The default is targeting forest and waterbodies.

If the folder contains .pgw files with the same name as a .png file, it can be read along with the .png. The script assumes the .pgw is the coordinates for the top left corner. The calculated coordinates of each photo will be stored with the color percentage data. 

The info is stored as a python dictionary, so data outputs are easy to create. pre-made options is the images with the info in the name, as .json and as .txt 


**Installation**

lol just setup python virtual environment *(or don't)*
and run ``` pip install -r requirements.txt ``` 

**Usage**

``` python ImageDatasetBuilder.py ``` runs the s.o.b.
To modify, just go to main and change the inputs or create your own doc with a main and import the ImageDatasetBuilder, preferably bob...

```python 
import ImageDatasetBuilder
bob = ImageDatasetBuilder()
bob.set_target('./img.png', pgw_file_path_if_any='img.pgw') 
# multiple files and folders can be targeted at once.
# if a matching pgw file is present, coordinates will be calculated.
bob.set_target_folder('./DK_imgs/', contains_pgw_files=True)
# optionally, save all split images to a folder. 
bob.build(output_split_images_to='./output/')
# multiple options for saving
bob.print_result()
bob.save_result_as_json()
bob.save_result_as_txt(save_path='./', save_file_name='have_a_nice_day.txt')
```


