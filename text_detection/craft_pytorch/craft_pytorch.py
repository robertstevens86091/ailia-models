import sys
import time

import cv2

import ailia
import craft_pytorch_utils

# import original modules
sys.path.append('../../util')
from utils import get_base_parser, update_parser  # noqa: E402
from model_utils import check_and_download_models  # noqa: E402
import webcamera_utils  # noqa: E402


# ======================
# Parameters
# ======================
WEIGHT_PATH = 'craft.onnx'
MODEL_PATH = 'craft.onnx.prototxt'
REMOTE_PATH = 'https://storage.googleapis.com/ailia-models/craft-pytorch/'

IMAGE_PATH = 'imgs/00_00.jpg'
SAVE_IMAGE_PATH = 'imgs_results/res_00_00.jpg'

THRESHOLD = 0.2
IOU = 0.2


# ======================
# Arguemnt Parser Config
# ======================
parser = get_base_parser(
    'CRAFT: Character-Region Awareness For Text detection',
    IMAGE_PATH,
    SAVE_IMAGE_PATH,
)
args = update_parser(parser)


# ======================
# Main functions
# ======================
def recognize_from_image():
    # prepare input data
    image = craft_pytorch_utils.load_image(args.input)
    print(f'input image shape: {image.shape}')
    x, ratio_w, ratio_h = craft_pytorch_utils.pre_process(image)

    # net initialize
    net = ailia.Net(MODEL_PATH, WEIGHT_PATH, env_id=args.env_id)
    net.set_input_shape((1, 3, x.shape[2], x.shape[3]))

    # inference
    print('Start inference...')
    if args.benchmark:
        print('BENCHMARK mode')
        for i in range(5):
            start = int(round(time.time() * 1000))
            y, _ = net.predict({'input.1': x})
            end = int(round(time.time() * 1000))
            print(f'\tailia processing time {end - start} ms')
    else:
        y, _ = net.predict({'input.1': x})

    img = craft_pytorch_utils.post_process(y, image, ratio_w, ratio_h)
    cv2.imwrite(args.savepath, img)
    print('Script finished successfully.')


def recognize_from_video():
    # net initialize
    net = ailia.Net(MODEL_PATH, WEIGHT_PATH, env_id=args.env_id)

    capture = webcamera_utils.get_capture(args.video)

    # create video writer if savepath is specified as video format
    if args.savepath != SAVE_IMAGE_PATH:
        f_h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        f_w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        writer = webcamera_utils.get_writer(args.savepath, f_h, f_w)
    else:
        writer = None

    while(True):
        ret, image = capture.read()
        # press q to end video capture
        if (cv2.waitKey(1) & 0xFF == ord('q')) or not ret:
            break

        x, ratio_w, ratio_h = craft_pytorch_utils.pre_process(image)
        net.set_input_shape((1, 3, x.shape[2], x.shape[3]))
        y, _ = net.predict({'input.1': x})
        img = craft_pytorch_utils.post_process(y, image, ratio_w, ratio_h)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', img)

        # save results
        if writer is not None:
            writer.write(img)

    capture.release()
    cv2.destroyAllWindows()
    if writer is not None:
        writer.release()
    print('Script finished successfully.')


def main():
    # model files check and download
    check_and_download_models(WEIGHT_PATH, MODEL_PATH, REMOTE_PATH)

    if args.video is not None:
        # video mode
        recognize_from_video()
    else:
        # image mode
        recognize_from_image()


if __name__ == '__main__':
    main()
