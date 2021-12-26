
T = 2;
led_width = 14;
led_thick = 5;
tank_lip_thick = 2.8;
clip_width = 5;
clip_depth = 5;


difference() {
    union() {
        cube([led_width+T*2, led_thick+2*T, clip_width]);
        
        rotate([0,0,45])
        translate([1,0,clip_width/2])
        cube([tank_lip_thick+2*T+2, clip_depth+2*T, clip_width], center=true);
        
        
    }
    translate([T,T,-1])
    cube([led_width, led_thick, 100]);
    for (i=[-1,1])
    translate([(led_width+T*2)/2+i*2,led_thick+2*T+1,-1])
    rotate([0,0,45])
    cube([10, 10, 100], center=true);


    rotate([0,0,45])
    translate([0,-T,clip_width/2])
    cube([tank_lip_thick, clip_depth+2*T, 100], center=true);

}