#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

from __future__ import division
import math
import pcbnew

import FootprintWizardBase

class QStrip_FootprintWizard(FootprintWizardBase.FootprintWizard):

    def GetName(self):
        return "Samtec Q Strip Terminal"
    
    def GetDescription(self):
        return "Samtec QTE/QTS/QTH High-Speed Ground Plane Terminal Strip Wizard"
    
    def GetValue(self):
        return "Samtec_QStrip"

    def GenerateParameterList(self):
        # Fabrication/silk layer configuration
        self.AddParam("Layout", "variant", r"Terminal,Socket", r"Terminal")
        self.AddParam("Layout", "connector height", self.uMM, 5.97)
        self.AddParam("Layout", "silkscreen offset", self.uMM, 0.25)
        # Pin bank configuration
        self.AddParam("Banks", "banks", self.uInteger, 3)
        self.AddParam("Banks", "pins per bank", self.uInteger, 60)
        self.AddParam("Banks", "width", self.uMM, 16.4)
        self.AddParam("Banks", "height", self.uMM, 3.9)
        self.AddParam("Banks", "spacing", self.uMM, 20.0)
        self.AddParam("Banks", "differential", self.uInteger, 0)
        # Signal pad parameters
        self.AddParam("Signal Pads", "pitch", self.uMM, 0.5)
        self.AddParam("Signal Pads", "width", self.uMM, 0.305)
        self.AddParam("Signal Pads", "height", self.uMM, 1.45)
        self.AddParam("Signal Pads", "y offset", self.uMM, 3.086)
        # Ground pad parameters
        self.AddParam("Ground Pads", "height", self.uMM, 0.64)
        self.AddParam("Ground Pads", "width (inner)", self.uMM, 4.7)
        self.AddParam("Ground Pads", "width (outer)", self.uMM, 2.54)
        self.AddParam("Ground Pads", "spacing (inner)", self.uMM, 6.35)
        self.AddParam("Ground Pads", "spacing (outer)", self.uMM, 16.89)
        # Hole parameters
        self.AddParam("Holes", "drill diameter", self.uMM, 1.02)
        self.AddParam("Holes", "pad diameter", self.uMM, 0.0)
        self.AddParam("Holes", "x offset", self.uMM, 1.989)
        self.AddParam("Holes", "y offset", self.uMM, 2.03)
        
    # Build a rectangular pad
    def smdRectPad(self,module,name,size,pos):
        pad = pcbnew.D_PAD(module)
        pad.SetSize(size)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetLayerSet(pad.SMDMask())
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetName(name)
        return pad

    # Build a hole
    def holePad(self,module,name,dia,ring_dia,pos):
        pad = pcbnew.D_PAD(module)
        pad.SetShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE)
        if ring_dia <= dia:
            # NPTH
            pad.SetAttribute(pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED)
            pad.SetLayerSet(pad.UnplatedHoleMask())
            pad.SetSize(pcbnew.wxSize(dia,dia))
            pad.SetDrillSize(pcbnew.wxSize(dia,dia))
        else:
            # PTH
            pad.SetAttribute(pcbnew.PAD_ATTRIB_STANDARD)
            pad.SetLayerSet(pad.StandardMask())
            pad.SetSize(pcbnew.wxSize(ring_dia,ring_dia))
            pad.SetDrillSize(pcbnew.wxSize(dia,dia))
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetName(name)
        return pad
    
    def CheckParameters(self):
        pass
    
    def BuildThisFootprint(self):
        variant = self.parameters["Layout"]["variant"]
        
        # Banks
        banks  = self.parameters["Banks"]["banks"]
        diff   = self.parameters["Banks"]["differential"]
        bank_x = self.parameters["Banks"]["spacing"]
        pins_per_bank = self.parameters["Banks"]["pins per bank"]

        # Get signal pad parameters
        pitch      = self.parameters["Signal Pads"]["pitch"]
        pad_width  = self.parameters["Signal Pads"]["width"]
        pad_height = self.parameters["Signal Pads"]["height"]
        pad_y = self.parameters["Signal Pads"]["y offset"]
        pad_size = pcbnew.wxSize(pad_width, pad_height)
        
        # Pin 1 position
        pin1 = pcbnew.wxPoint(0,0)
        pin1.x = int(-(pins_per_bank / 4)*pitch + pitch/2 - ((banks-1) / 2)*bank_x)
        if variant == "Terminal":
            pin1.y = -pad_y
        elif variant == "Socket":
            pin1.y = pad_y
        
        
        # Bank 1 center point
        bank1_mid = pin1.x - pitch/2 + (pins_per_bank / 4)*pitch
        
        # Place signal pads
        n = 1 # Pin counter
        for b in range(0, banks):
            for p in range(0, pins_per_bank):
                # Compute next pad location
                pos = pcbnew.wxPoint(pin1.x + (p // 2)*pitch + b*bank_x,
                                     pin1.y - (p  % 2)*(2*pin1.y))
                if b < diff and ((p+1) % 6 == 0 or (p+2) % 6 == 0):
                    # Place gaps between differential pairs
                    continue
                else:
                    # Create pad (both single-ended and differential)
                    pad = self.smdRectPad(self.module, str(n), pad_size, pos)
                    self.module.Add(pad)
                    n = n + 1
        
        # Ground pad parameters
        gnd_height    = self.parameters["Ground Pads"]["height"]
        gnd_width_in  = self.parameters["Ground Pads"]["width (inner)"]
        gnd_width_out = self.parameters["Ground Pads"]["width (outer)"]
        gnd_space_in  = self.parameters["Ground Pads"]["spacing (inner)"] / 2
        gnd_space_out = self.parameters["Ground Pads"]["spacing (outer)"] / 2
        gnd_space = [-gnd_space_out, -gnd_space_in, gnd_space_in, gnd_space_out]
        gnd_size  = [pcbnew.wxSize(gnd_width_out, gnd_height),
                     pcbnew.wxSize(gnd_width_in, gnd_height),
                     pcbnew.wxSize(gnd_width_in, gnd_height),
                     pcbnew.wxSize(gnd_width_out, gnd_height)]
        
        # Place ground plane pads
        for b in range(banks):
            mid = bank1_mid + b*bank_x # Bank midpoint
            for i in range(len(gnd_space)):
                pos = pcbnew.wxPoint(mid + gnd_space[i], 0)
                pad = self.smdRectPad(self.module, str(n), gnd_size[i], pos)
                self.module.Add(pad)
                n = n + 1
                           
        # Hole parameters
        hole_dia  = self.parameters["Holes"]["drill diameter"]
        hole_ring = self.parameters["Holes"]["pad diameter"]
        hole_offset = pcbnew.wxPoint(self.parameters["Holes"]["x offset"],
                                     self.parameters["Holes"]["y offset"])
        if variant == "Terminal":
            hole_offset.y = -hole_offset.y

        # Place holes
        for m in (-1,1):
            pos = pcbnew.wxPoint(m*(pin1.x-hole_offset.x), hole_offset.y)
            hole = self.holePad(self.module, "", hole_dia, hole_ring, pos)
            self.module.Add(hole)
            
        # Fab
        fab_height = self.parameters["Layout"]["connector height"] / 2
        fab_bank_height = self.parameters["Banks"]["height"]
        silk_offset = self.parameters["Layout"]["silkscreen offset"]
        silk_grid = pcbnew.ToMM(silk_offset)
                           
        # Configure F.Fab layer
        self.draw.SetLineThickness(pcbnew.FromMM(0.1)) # Default per KLC F5.2
        self.draw.SetLayer(pcbnew.F_Fab)
                           
        # Draw Bank cutouts
        for b in range(0,banks):
            mid = pcbnew.wxPoint(bank1_mid + b*bank_x, 0)
            # Bank cutout
            self.draw.Box(mid.x, mid.y, 2*gnd_space_out, fab_bank_height)
                           
        # Draw connector outline
        leftEdge = -banks*bank_x/2
        chamfer_x = bank1_mid - gnd_space_out
        chamfer = chamfer_x - leftEdge
        fabEndPoints = [(0, -fab_height),
                        (leftEdge, -fab_height),
                        (leftEdge, fab_height - chamfer),
                        (chamfer_x, fab_height),
                        (0, fab_height)]
        self.draw.Polyline(fabEndPoints, mirrorX = 0)

        # Pin 1 marker
        self.draw.MarkerArrow(pin1.x, -fab_height+pitch/2, self.draw.dirS, pitch)

        # Configure F.SilkS layer
        self.draw.SetLineThickness(pcbnew.FromMM(0.12)) # KLC5.1, per IPC-7351C
        self.draw.SetLayer(pcbnew.F_SilkS)
        
        # Draw silkscreen outline
        silkEdge = [(pin1.x - pad_width - silk_offset, pin1.y - silk_offset - pad_height/3),
                    (pin1.x - pad_width - silk_offset, pin1.y - silk_offset),
                    (leftEdge - silk_offset, pin1.y - silk_offset),
                    (leftEdge - silk_offset, fab_height - chamfer),
                    (chamfer_x, fab_height + silk_offset),
                    (pin1.x - pad_width - silk_offset, fab_height + silk_offset)]
        silkEdge_grid = []
        for point in silkEdge:
            silkEdge_grid.append((pcbnew.PutOnGridMM(point[0], silk_grid),
                                  pcbnew.PutOnGridMM(point[1], silk_grid)))

        self.draw.Polyline(silkEdge_grid[0:2]) # Draw Pin 1 indicator
        self.draw.Polyline(silkEdge_grid[1:], mirrorX = 0) # Draw connector outline
        # Draw side outlines between banks
        silk_x = bank1_mid - silkEdge_grid[0][0]
        silk_y = silkEdge_grid[-1][1]
        for b in range(0,banks-1):
            mid = bank1_mid + b*bank_x
            x0 = mid + silk_x
            x1 = mid + bank_x/2
            x2 = x1 - x0
            silkOutline = [(x0, silk_y),
                           (x1+x2, silk_y)]
            self.draw.Polyline(silkOutline, mirrorY = 0)
            
        # Configure courtyard layer
        self.draw.SetLayer(pcbnew.F_CrtYd)
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))

        # Draw courtyard
        #crtyd_width = self.parameters["Layout"]["courtyard width"]
        #crtyd_height = self.parameters["Layout"]["courtyard height"]
        #self.draw.Box(0, 0, crtyd_width, crtyd_height)
        
        self.module.SetAttributes(pcbnew.MOD_CMS)
        
QStrip_FootprintWizard().register()
