import modules.scripts as scripts
import modules.images
import gradio as gr
from PIL import Image
from modules.processing import Processed, process_images

#Get num closest to 8
def cl8(num):
    rem = num % 8
    if rem <= 4:
        return round(num - rem)
    else:
        return round(num + (8 - rem))

def normalize_size(images):
    refimage = images[0]
    refimage = refimage.resize((cl8(refimage.width), cl8(refimage.height)), Image.Resampling.LANCZOS)
    return_images = [refimage]
    for i in range(len(images[1:])):
        if images[i].size != refimage.size:
            images[i] = images[i].resize(refimage.size, Image.Resampling.LANCZOS)
        return_images.append(images[i])
    return return_images

def constrain_image(image, max_width, max_height):
    width, height = image.size
    aspect_ratio = width / float(height)

    if width > max_width or height > max_height:
        if width / float(max_width) > height / float(max_height):
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)
        image = image.resize((cl8(new_width), cl8(new_height)), Image.Resampling.LANCZOS)

    return image

def padlist(lst, targetsize):
    if targetsize <= len(lst):
            return lst[:targetsize]

    last_elem = lst[-1]
    num_repeats = targetsize - len(lst)
    
    return lst + [last_elem] * num_repeats

def MakeGrid(images, rows, cols):
    widths, heights = zip(*(i.size for i in images))

    grid_width = max(widths) * cols
    grid_height = max(heights) * rows
    cell_width = grid_width // cols
    cell_height = grid_height // rows
    final_image = Image.new('RGB', (grid_width, grid_height))
    x_offset = 0
    y_offset = 0
    for i in range(len(images)):
        final_image.paste(images[i], (x_offset, y_offset))
        x_offset += cell_width
        if x_offset == grid_width:
            x_offset = 0
            y_offset += cell_height

    # Save the final image
    return final_image

def BreakGrid(grid, rows, cols):
    width = grid.width // cols
    height = grid.height // rows
    outimages = []
    for row in range(rows):
            for col in range(cols):
                left = col * width
                top = row * height
                right = left + width
                bottom = top + height
                current_img = grid.crop((left, top, right, bottom))
                outimages.append(current_img)
    return outimages

class Script(scripts.Script):
    def __init__(self):
        #self.frame2frame_dir = tempfile.TemporaryDirectory()
        self.img2img_component = gr.Image()
        self.img2img_inpaint_component = gr.Image()
        self.img2img_w_slider = gr.Slider()
        self.img2img_h_slider = gr.Slider()
        return None

    def title(self):
        return "keyframer"

    def show(self, is_img2img):
        return is_img2img
    
    def ui(self, is_img2img):
        #Controls
        with gr.Column():
            with gr.Row():
                with gr.Box():
                    with gr.Column():
                        input_upload = gr.Files(label = "Drop or select keyframe files")
                    with gr.Column():
                        with gr.Row():
                            with gr.Column():
                                gen_rows = gr.Slider(2, 20, 8, step=2, label="Grid rows", interactive=True)
                                gen_cols = gr.Slider(2, 20, 8, step=2, label="Grid columns", interactive=True)
                                gen_maxwidth = gr.Slider(64, 3992, 2048, step=8, label="Maximum generation width", interactive=True, elem_id="maxwidth")
                                gen_maxheight = gr.Slider(64, 3992, 2048, step=8, label="Maximum generation height", interactive=True, elem_id="maxheight")
                            with gr.Column():
                                info_width = gr.Number(label="width", interactive=False)
                                info_height = gr.Number(label="height", interactive=False)
            gen_button = gr.Button("Generate sheet")
            gen_image = gr.Image(Source="Upload", label = "Preview", type= "filepath", interactive=False)

        def submit_images(files, rows, cols, maxwidth, maxheight):
            if files == None:
                return gr.Image.update(), gr.Image.update(), gr.Image.update(), gr.Slider.update(), gr.Slider.update(), gr.Number.update(), gr.Number.update()
            else:
                imageslist = []
                for file in files:
                    try:
                        imageslist.append(Image.open(file.name))
                    except: pass
                if len(imageslist) < 2:
                    print("keyframer: Not enough valid images found in input (need at least two)")
                    return gr.Image.update(), gr.Image.update(), gr.Image.update(), gr.Slider.update(), gr.Slider.update(), gr.Number.update(), gr.Number.update()
                else:
                    imageslist = normalize_size(imageslist)
                    imageslist = padlist(imageslist, (rows*cols))
                    grid = MakeGrid(imageslist, rows, cols)
                    grid = constrain_image(grid, maxwidth, maxheight)
                    return grid, grid, grid, grid.width, grid.height, grid.width, grid.height

        gen_button.click(fn=submit_images, inputs=[input_upload, gen_rows, gen_cols, gen_maxwidth, gen_maxheight], outputs=[gen_image, self.img2img_component, self.img2img_inpaint_component, self.img2img_w_slider, self.img2img_h_slider, info_width, info_height])

        return [gen_rows, gen_cols, info_width, info_height]
    
    #Grab the img2img image components for update later
    #Maybe there's a better way to do this?
    def after_component(self, component, **kwargs):
        if component.elem_id == "img2img_image":
            self.img2img_component = component
            return self.img2img_component
        if component.elem_id == "img2maskimg":
            self.img2img_inpaint_component = component
            return self.img2img_inpaint_component
        if component.elem_id == "img2img_width":
            self.img2img_w_slider = component
            return self.img2img_w_slider
        if component.elem_id == "img2img_height":
            self.img2img_h_slider = component
            return self.img2img_h_slider
        
    #Main run
    def run(self, p, gen_rows, gen_cols, info_width, info_height):

        p.do_not_save_grid = True
        p.width = int(info_width)
        p.height = int(info_height)
        p.control_net_lowvram = True
        p.control_net_resize_mode = "Just Resize"
        if p.init_images[0].height > p.init_images[0].width:
            p.control_net_pres = p.init_images[0].height
        else:
            p.control_net_pres = p.init_images[0].width
        proc = process_images(p) #process
        image_frames = []
        for grid in proc.images:
            image_frames.extend(BreakGrid(grid, gen_rows, gen_cols))
        return_images = []
        for frame in image_frames:
            out_filename = (modules.images.save_image(frame, p.outpath_samples, "keyframe", extension = 'png')[0])
            return_images.append(out_filename)

        return Processed(p, return_images, p.seed, "", all_prompts=proc.all_prompts, infotexts=proc.infotexts)