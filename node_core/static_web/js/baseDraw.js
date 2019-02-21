
//绘制标注类
/*
* @param 
*/

/*const app = new Vue({
  el: '#app',
  data: {
    frame_id: -1,
    lw_dis: 0,
    rw_dis: 0
  }
})*/

class DrawLabel{
    static draw(ctx, label_data){
        var vehicle = label_data['vehicle'] || {};
        var lane = label_data['lane'] || {};
        var ped = label_data['ped'] || {};
        var tsr = label_data['tsr'] || {};
        this.drawVehicle(ctx, vehicle);
        this.drawLane(ctx, lane);
        this.drawPed(ctx, ped);
        this.drawTsr(ctx, tsr);
    }

    static drawVehicle(ctx, vehicle_data){
        var dets = vehicle_data['dets'] || [];
        var focus_index = vehicle_data['focus_index'];
        for(let i =0; i<dets.length; i++){
            let det = dets[i];
            let bounding_rect = det['bounding_rect'];
            let x = bounding_rect['x'];
            let y = bounding_rect['y'];
            let width = bounding_rect['width'];
            let height = bounding_rect['height'];
            let color = focus_index===i ? 'rgb(255,0,0)' : 'rgb(255,255,0)';
            BaseDraw.strokeRect(ctx, [x, y, width, height], color, 2);
        }
    }

    static drawLane(ctx, lane_data){
        const lanelines = lane_data['lanelines'] || [];
        // app.lw_dis = lane_data['left_wheel_dist'].toFixed(2)
        // app.rw_dis = lane_data['right_wheel_dist'].toFixed(2)
        for(let i=0;i<lanelines.length; i++){
            let lane = lanelines[i];
            let color = 'rgb(255,255, 0)';
            let width = lane['width'];
            let ratios = lane['perspective_view_poly_coeff'];
            // width = Math.floor(width*5.0+0.5);
            width = 3;

            let a0 = ratios[0];
            let a1 = ratios[1];
            let a2 = ratios[2];
            let a3 = ratios[3];
            for(let y=500; y<720; y+=20){
                let y1 = y;
                let y2 = y1 + 20;
                let x1 = Math.floor(a0 + a1*y1 + a2*y1*y1 + a3*y1*y1*y1);
                let x2 = Math.floor(a0 + a1*y2 + a2*y2*y2 + a3*y2*y2*y2);
                BaseDraw.drawLine(ctx, [x1, y1, x2, y2], color, width);
            }
        }
    }

    static drawPed(ctx, ped_data){
        var pedestrians = ped_data['pedestrians'] || [];
        for(let ped of pedestrians){
            let box = ped['regressed_box'];
            let x = box['x'];
            let y = box['y'];
            let w = box['width'];
            let h = box['height'];
            let color = ped['is_key'] ? 'rgb(255,0,0)' : 'rgb(255,255,0)';
            BaseDraw.strokeRect(ctx, [x, y, w, h], color, 1);
        }
    }

    static drawTsr(ctx, tsr_data){
        var dets = tsr_data['dets'] || [];
        for(let det of dets){
            let p = det['position'];
            let x = p['x'];
            let y = p['y'];
            let w = p['width'];
            let h = p['height'];
            let color = 'rgb(255,0,0)';
            BaseDraw.strokeRect(ctx, [x, y, w, h], color, 1);
        }
    }
}

//基础绘图类

class BaseDraw{
    static drawLine(ctx, position, color='rgb(255,0,0)', lineWidth=1){
        var x0 = position[0];
        var y0 = position[1];
        var x1 = position[2];
        var y1 = position[3];
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = color;
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.stroke();
    }

    static strokeRect(ctx, position, color='rgb(255,0,0)', lineWidth=1){
        var x = position[0];
        var y = position[1];
        var width = position[2];
        var height = position[3];
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = color;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.rect(x, y, width, height);
        ctx.stroke();
    }
}