#!/usr/bin/env python3
"""
"""
import cv2
import numpy as np

class CVColor(object):
    '''
    basic color RGB define
    '''
    Red = (0, 0, 255)
    Green = (0, 255, 0)
    Blue = (255, 0, 0)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Yellow = (0, 255, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Pink = (255, 0, 255)

class BaseDraw(object):
    """
    """

    @classmethod
    def draw_text(cls, img_content, text, position, size, color, thickness, type=cv2.LINE_AA):
        """
        For anti-aliased text, add argument cv2.LINE_AA.
        sample drawText(img_content, text, (20, 30), 0.6, CVColor.Blue, 2)
        """
        cv2.putText(img_content, text, position,
                    cv2.FONT_HERSHEY_SIMPLEX, size, color,
                    thickness, type)
    
    @classmethod
    def draw_rect(cls, img_content, point1, point2, color, thickness=2):
        cv2.rectangle(img_content, point1, point2, color, thickness)

    @classmethod
    def draw_vehicle_rect_corn(cls, img, point1, point2, color, thickness=2):
        """
            draw 8 lines at corns
        """
        x1, y1 = point1
        x2, y2 = point2
        width = abs(x2-x1)
        height = abs(y2-y1)
        suit_len = min(width, height)
        suit_len = int(suit_len / 6)
        
        # 左上角
        cv2.line(img, (x1,y1), (x1+suit_len, y1), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x1,y1), (x1, y1+suit_len), color, thickness, cv2.LINE_8, 0)

        # 右上角
        cv2.line(img, (x2-suit_len,y1), (x2, y1), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x2,y1), (x1+width, y1+suit_len), color, thickness, cv2.LINE_8, 0)

        # 左下角
        cv2.line(img, (x1,y2-suit_len), (x1, y2), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x1,y2), (x1+suit_len, y2), color, thickness, cv2.LINE_8, 0)

        # 右下角
        cv2.line(img, (x2-suit_len,y2), (x2, y2), color, thickness, cv2.LINE_8, 0)
        cv2.line(img, (x2,y2-suit_len), (x2, y2), color, thickness, cv2.LINE_8, 0)


    @classmethod
    def draw_line(cls, img_content, p1, p2,  color_type = CVColor.White, thickness=1, type=cv2.LINE_8):
        cv2.line(img_content, p1, p2, color_type, thickness, type, 0)

    @classmethod
    def draw_lane_line(cls, img_content, line,  color_type='',
                       begin=420, end=650):
        """
        g = a0 + a1*x + a2*x*x + a3*x*x*x
        a0 = -28.0362
        a1 = 1.42638
        a2 = -2.64114e-05
        a3 = 0
        """
        a0 = float(line[0])
        a1 = float(line[1])
        a2 = float(line[2])
        a3 = float(line[3])

        for x in range(begin, end, 10):
            y = int(a0 + a1*x + a2*x*x + a3*x*x*x)
            x1 = x + 10
            y1 = int(a0 + a1*x1 + a2*x1*x1 + a3*x1*x1*x1)
            cv2.line(img_content, (y, x), (y1, x1), CVColor.White, 2,
                     cv2.LINE_AA, 0)

    @classmethod
    def draw_alpha_rect(cls, image_content, rect, alpha, color = CVColor.White, line_width = 0):
        x, y, w, h = rect
        img = np.zeros((h, w, 3), np.uint8)
        roi = image_content[y:y+h, x:x+w]
        cv2.addWeighted(img, 1.0, roi, alpha, 0.0, roi)
        if line_width > 0:
            cv2.rectangle(image_content, (x, y), (x+w, y+h), color, line_width)
