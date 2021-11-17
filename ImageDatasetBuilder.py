import os
import cv2
import numpy as np
import json
import pprint
import time


class PwgCoordinateExtrapolator:
    def __init__(self, pgw_filepath: str, slice_size_x: int, img_size_x: int):
        self.skip = slice_size_x
        self.img_size_x = img_size_x
        
        lines = []
        with open(pgw_filepath) as f:
            lines = f.readlines()
        self.A = float(lines[0])
        self.D = float(lines[1])
        self.B = float(lines[2])
        self.E = float(lines[3])
        self.C = float(lines[4])
        self.F = float(lines[5])

        self.current_x = 0
        self.current_y = 0


    def get_next(self):
        top_left = self.calc_coordinates(self.current_x, self.current_y)
        butt_right = self.calc_coordinates(self.current_x + self.skip, self.current_y + self.skip)
        self.current_x += self.skip
        if self.current_x - 1 >= self.img_size_x - self.skip:
            self.current_y += self.skip
            self.current_x = 0
        return top_left, butt_right


    
    def calc_coordinates(self, x, y):
        x1 = self.A*x + self.B*y + self.C
        y1 = self.D*x + self.E*y + self.F
        return y1, x1


class ImageDatasetBuilder:
    def __init__(self):
        self.dataset_dict: dict = {}
        self.pgw_files = []
        self.img_files = []

    """
    Load Single (optional: pgw file) -done
    Load folder (optional: pgw file) -done
    
    Split image -done

    # pgw handling
        calc top-left corner
        calc each new corner
    
    calc percentage forest, water -done
    
    output console print -done
    Output json? -done
    Output split images? stats in filename? -done
    Output txt? -done
    """

    def set_target(self, file_path: str, pgw_file_path_if_any: str=''):
        self.img_files.append(file_path)
        if pgw_file_path_if_any:
            self.pgw_files.append(pgw_file_path_if_any)


    def set_target_folder(self, folder_path: str, contains_pgw_files=False):
        sorted_dir = sorted(os.listdir(folder_path))

        for filename in sorted_dir:
            if filename.endswith('.png') or filename.endswith('.jpg'):
                self.img_files.append(folder_path + filename)
            elif contains_pgw_files and filename.endswith('.pgw'):
                self.pgw_files.append(folder_path + filename)
    

    def build(self, split_to_squares_px: int=250, output_split_images_to=''):
        build_t0 = time.time()
        total_split_imgs = 0

        for filepath in self.img_files:
            t0 = time.time()
            
            filename = list(reversed(filepath.split('/')))[0].split('.')[0] # i hate this line

            print('Starting on', filename)

            _img = cv2.imread(filepath) # numpy array
            
            img_cluster_arr = self._slice_img(_img, split_to_squares_px, split_to_squares_px)
            print('Split image into:', len(img_cluster_arr), 'pieces')
            total_split_imgs += len(img_cluster_arr)

            # pgw handling class instance
            coordinator = None
            if pgw_path := self._get_pgw_if_any(filepath): # shitty solution but eh.
                height, width = _img.shape[:2] 
                coordinator = PwgCoordinateExtrapolator(pgw_path, split_to_squares_px, width)

            for i, img_arr in enumerate(img_cluster_arr):
                green_msk = self._mask(img_arr, sensitivity=100, rgb_lower=[0, 30, 0], rgb_upper=[70, 100, 70])
                blue_msk = self._mask(img_arr, sensitivity=85, rgb_lower=[50, 100, 60], rgb_upper=[50, 255, 255]) 
                tree_percentage = self._calcPercentage(green_msk)
                water_percentage = self._calcPercentage(blue_msk)

                # pgw handling and coordinate retrieval.
                top_left, butt_right = None, None
                if coordinator:
                    top_left, butt_right = coordinator.get_next()

                new_name = filename + '_' + str(i)
                img_data = { new_name: {'tree': tree_percentage, 'water': water_percentage, 'top_left': top_left, 'butt_right': butt_right}}
                self.dataset_dict.update(img_data)

                if output_split_images_to and top_left:
                    cv2.imwrite(output_split_images_to + new_name + f'_tree-{int(tree_percentage)}_water-{int(water_percentage)}_NE_{top_left[0]}_{top_left[1]}.png', img_arr)
                elif output_split_images_to:
                    cv2.imwrite(output_split_images_to + new_name + f'_tree-{int(tree_percentage)}_water-{int(water_percentage)}.png', img_arr)



            print(filename, 'finished in', time.time() - t0, 'seconds')
            if output_split_images_to:
                print(len(img_cluster_arr), 'images saved to' + output_split_images_to)

        print('Building', total_split_imgs, 'images finished in', time.time() - build_t0, 'seconds')


    def print_result(self):
        pprint.pprint(json.dumps(self.dataset_dict))
    

    def save_result_as_json(self, save_path: str='./', save_file_name: str='data.json'):
        with open(save_path + save_file_name, 'w') as fp:
            json.dump(self.dataset_dict , fp)
    

    def save_result_as_txt(self, save_path: str='./', save_file_name: str='data.txt'):
        with open(save_path + save_file_name, 'w') as fp:
            for line in self.dataset_dict.items():
                fp.write(str(line))
                fp.write('\n')


    def _calcPercentage(self, msk): 
	    ''' 
	    returns the percentage of white in a binary image 
	    ''' 
	    height, width = msk.shape[:2] 
	    num_pixels = height * width 
	    count_white = cv2.countNonZero(msk) 
	    percent_white = (count_white/num_pixels) * 100 
	    percent_white = round(percent_white,2) 
	    return percent_white 
            

    def _slice_img(self, im: np.array , M: int, N: int):
        return [im[x:x+M,y:y+N] for x in range(0,im.shape[0],M) for y in range(0,im.shape[1],N)]


    def _mask(self, img, sensitivity: int=20, rgb_lower=[50, 100, 60], rgb_upper=[50, 255, 255]):
        # mask define... *might* be green
        lower_bound = np.array([rgb_lower[0] - sensitivity, rgb_lower[1], rgb_lower[2]]) 
        upper_bound = np.array([rgb_upper[0] + sensitivity, rgb_upper[1], rgb_upper[2]]) 
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        msk = cv2.inRange(img_hsv, lower_bound, upper_bound)
        return msk
    
    
    def _get_pgw_if_any(self, png_path):
        pgw_name = png_path[: -4] + '.pgw'
        if pgw_name in self.pgw_files:
            return pgw_name


#for testing purposes
if __name__ == '__main__':
    bob = ImageDatasetBuilder()
    # bob.set_target('./DK_imgs/DenmarkRound01.png', './DK_imgs/DenmarkRound01.pgw')
    bob.set_target_folder('./DK_imgs/', contains_pgw_files=True)
    bob.build()
    # bob.build(output_split_images_to='./output/')
    # bob.print_result()
    bob.save_result_as_json()
    # bob.save_result_as_txt()

"""
These lines of stupid rgb color masking codes is stupid, dont loose them, i will not make them again.

green_msk = self._mask(img_arr, sensitivity=100, rgb_lower=[0, 30, 0], rgb_upper=[70, 100, 70])
blue_msk = self._mask(img_arr, sensitivity=85, rgb_lower=[50, 100, 60], rgb_upper=[50, 255, 255]) 
"""