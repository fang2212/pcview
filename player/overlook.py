import cv2
import numpy as np

class OverlookPlayer():
    def __init__(self, name="img", w=600, h=1000):
        self.name = name
        self.width = w
        self.height = h
        self.dx = w / 10.8
        self.dy = h / 150
        self.background = self.get_background(w,h)
        self.reset()

    def draw(self, mess):
        if 'vehicle_measure_res_list' in mess:
            self.draw_vehicle(mess['vehicle_measure_res_list'])
        return self.get()

    def __del__(self):
        pass

    def get_background(self, w, h):
        col, row = 3, 10
        img = np.ones((h+60,w+60,3), np.uint8)
        img = img * 200
        for i in range(0, w+1, int(w/col)):
            self.draw_line(img, (i+30, 30), (i+30, h+30))
        for i in range(0, h+1, int(h/row)):
            self.draw_line(img, (30,i+30), (w+30, i+30))
        for i in range(-54, 55, 36):
            px, py = int(15+self.width/2+i/10*self.dx), self.height + 30 + 15
            self.draw_text(img, "%.1fm"%(i/10), (px,py))
        for i in range(15, 151, 15):
            px, py = self.width+32, int(self.height-i*self.dy+30)
            self.draw_text(img, "%dm"%i, (px,py))
            
        return img

    def shape(self):
        return (self.img.shape[1], self.img.shape[0])

    def reset(self):
        self.img = self.background.copy()
        self.palette = self.img[30:-30,30:-30]
    
    def show(self):
        self.writer.write(self.img)
        cv2.imshow(self.name, self.img)
        cv2.waitKey(1)
        self.reset()

    def get(self):
        copy = self.img.copy()
        self.reset()
        return copy

    def draw_line(self, img, pt1, pt2, thickness=1):
        cv2.line(img, pt1, pt2, (30,30,30), thickness)

    def draw_text(self, img, text, pos):
        cv2.putText(img, text, pos,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (30,30,30),
                    1)

    def draw_car(self, x, y, color=(0, 0, 250), size=5, thickness=2):
        cv2.rectangle(self.palette, (x-size*2, y-size), (x+size*2, y+size), color, thickness)

    def draw_vehicle(self, vehicle_data):
        for vehicle in vehicle_data:
            is_crucial = vehicle['is_crucial']
            if is_crucial:
                color = (0, 0, 250)
            else:
                color = (250, 0, 0)
            x, y = vehicle['lateral_dist'], vehicle['longitude_dist']
            x = int(self.width/2 + x * self.dx)
            y = int(self.height - y * self.dy)
            self.draw_car(x, y, color, 5)