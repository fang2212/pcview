from player import ui
from tools import transform

class Player(object):
    def __init__(self):
        self.color_list = [ui.CVColor.Red, ui.CVColor.Green, ui.CVColor.Cyan,
                           ui.CVColor.Magenta, ui.CVColor.Yellow, ui.CVColor.Black, ui.CVColor.Pink]

    def draw_front_camera_meas(self, img, item, color):
        rect = item['bounding_rect']
        x, y, w, h = int(rect['x']), int(rect['y']), int(rect['width']), int(rect['height'])
        ui.BaseDraw.draw_alpha_rect(img, (x, y, w, h), 0.8, color)
        ui.BaseDraw.draw_text(img, str(item['id']), (x, y - 5), 0.8, color, 1)
        if item['cipv']:
            ui.BaseDraw.draw_rect_corn(img, (x, y), (x + w, y + h), ui.CVColor.Blue)

    def draw_front_radar_meas(self, img, item, color):
        x, y, id = item['vertical_dist'], item['horizontal_dist'], item['id']
        ix, iy = transform.trans_gnd2raw(x, y)
        ix, iy = int(ix), int(iy)
        ui.BaseDraw.draw_circle(img, position=(ix, iy), color=color)
        ui.BaseDraw.draw_text(img, str(id), (ix, iy - 5), 0.5, color, 1)

    def draw_top_camera_meas(self, img, item, color):
        x, y, id = item['vertical_dist'], item['horizontal_dist'], item['id']
        ix, iy = transform.trans_gnd2ipm(x, y)
        ix, iy = int(ix), int(iy)
        ui.BaseDraw.draw_line(img, (ix-4, iy-4), (ix+4, iy+4), color_type=color)
        ui.BaseDraw.draw_line(img, (ix+4, iy-4), (ix-4, iy+4), color_type=color)
        ui.BaseDraw.draw_text(img, str(id), (ix, iy), 0.5, color, 1)

    def draw_top_radar_meas(self, img, item, color):
        x, y, id = item['vertical_dist'], item['horizontal_dist'], item['id']
        ix, iy = transform.trans_gnd2ipm(x, y)
        ix, iy = int(ix), int(iy)
        ui.BaseDraw.draw_circle(img, (ix, iy), color=color)
        ui.BaseDraw.draw_text(img, str(id), (ix, iy - 5), 0.5, color, 1)

    def draw_ipm_background(self, ipm):
        for x in range(10, 210, 10):
            ix, iy = transform.trans_gnd2ipm(x, 0)
            ui.BaseDraw.draw_line(ipm, (10, iy), (470, iy), ui.CVColor.Magenta)
            ui.BaseDraw.draw_text(ipm, "%dm"%x, (0, iy), 0.3, ui.CVColor.Magenta, 1)

    def draw(self, img, ipm, data):
        mea, fusion, img_data = data
        self.draw_ipm_background(ipm)

        speed = 0
        if "ego_car" in mea and mea['ego_car']['is_speed_valid']:
            speed = mea['ego_car']['speed']
        
        ui.BaseDraw.draw_text(img, "frame_no:%d" % img_data['img_frame_id'], (10, 50), 0.8, ui.CVColor.Red, 1)
        if mea:
            ui.BaseDraw.draw_text(img, "speed:%.2f km/h" % speed, (10, 25), 0.8, ui.CVColor.Red, 1)
            ui.BaseDraw.draw_text(img, "frame_no:%d" % mea['img_frame_id'], (10, 50), 0.8, ui.CVColor.Red, 1)

        if 'camera_meas' in mea:
            for item in mea['camera_meas']:
                self.draw_front_camera_meas(img, item, ui.CVColor.White)
                self.draw_top_camera_meas(ipm, item, ui.CVColor.White)

        if 'radar_meas' in mea:
            for item in mea['radar_meas']:
                self.draw_front_radar_meas(img, item, ui.CVColor.Black)
                self.draw_top_radar_meas(ipm, item, ui.CVColor.Black)

        if 'fusion_tracks' in fusion:
            fusion_tracks = fusion['fusion_tracks']
            deleted_tracks = fusion['deleted_tracks']
            new_tracks = fusion['new_tracks']

            deleted_ids = []
            for i in range(len(deleted_tracks)):
                x, y = 1000, (i + 1) * 20
                id = deleted_tracks[i]['id']
                ui.BaseDraw.draw_text(img, "x fid: %d" % id, (x, y), 0.5, ui.CVColor.Black, 1)
                deleted_ids.append(deleted_tracks[i])

            for i in range(len(fusion_tracks)):
                id = fusion_tracks[i]['id']
                if id in deleted_ids:
                    continue

                color = self.color_list[id % 7]
                x, y = fusion_tracks[i]['vertical_dist'], fusion_tracks[i]['horizontal_dist']
                ix, iy = transform.trans_gnd2raw(x, y)
                ix, iy = int(ix), int(iy)
                ui.BaseDraw.draw_rect(img, (ix - 5, iy - 5), (ix + 5, iy + 5), color)
                ui.BaseDraw.draw_text(img, str(id), (ix, iy), 0.5, color, 1)

                ix, iy = transform.trans_gnd2ipm(x, y)
                ix, iy = int(ix), int(iy)
                ui.BaseDraw.draw_rect(ipm, (ix - 5, iy - 5), (ix + 5, iy + 5), color)
                ui.BaseDraw.draw_text(ipm, str(id), (ix, iy), 0.5, color, 1)

                if 'asso_info' in fusion_tracks[i]:
                    if 'asso_camera_data' in fusion_tracks[i]['asso_info']:
                        item = fusion_tracks[i]['asso_info']['asso_camera_data']['camera_mea']
                        self.draw_front_camera_meas(img, item, color)
                        self.draw_top_camera_meas(ipm, item, color)

                    if 'asso_radar_data' in fusion_tracks[i]['asso_info']:
                        item = fusion_tracks[i]['asso_info']['asso_radar_data']['radar_mea']
                        self.draw_front_radar_meas(img, item, color)
                        self.draw_top_radar_meas(ipm, item, color)

        if 'gt_data' in mea:
            x, y = mea['gt_data']['vertical_dist'], mea['gt_data']['horizontal_dist']
            ix, iy = transform.trans_gnd2raw(x, y)
            ix, iy = int(ix), int(iy)
            ui.BaseDraw.draw_line(img, (ix-10, iy), (ix+10, iy), ui.CVColor.Green)
            ui.BaseDraw.draw_line(img, (ix, iy-10), (ix, iy+10), ui.CVColor.Green)

            ix, iy = transform.trans_gnd2ipm(x, y)
            ix, iy = int(ix), int(iy)
            ui.BaseDraw.draw_line(ipm, (ix - 5, iy), (ix + 5, iy), ui.CVColor.Green)
            ui.BaseDraw.draw_line(ipm, (ix, iy - 5), (ix, iy + 5), ui.CVColor.Green)
