# File: incidents/management/commands/populate_dropdown_data.py
from django.core.management.base import BaseCommand
from incidents.models import DropdownConfiguration

class Command(BaseCommand):
    help = 'Populate dropdown configuration data for all network types'

    def handle(self, *args, **options):
        self.stdout.write('Populating dropdown configuration data...')
        
        # Clear existing data (optional - remove this line to preserve existing data)
        # DropdownConfiguration.objects.all().delete()
        
        sample_data = [
            # Common - Causes
            ('cause', 'Power Failure', 1),
            ('cause', 'Fiber Cut', 2),
            ('cause', 'Equipment Failure', 3),
            ('cause', 'Software Bug', 4),
            ('cause', 'Human Error', 5),
            ('cause', 'Natural Disaster', 6),
            ('cause', 'Planned Maintenance', 7),
            ('cause', 'Network Congestion', 8),
            ('cause', 'Security Breach', 9),
            ('cause', 'Other', 99),
            
            # Common - Origins
            ('origin', 'Internal System', 1),
            ('origin', 'External Provider', 2),
            ('origin', 'Customer Site', 3),
            ('origin', 'Data Center', 4),
            ('origin', 'Field Equipment', 5),
            ('origin', 'Third Party', 6),
            ('origin', 'Unknown', 7),
            ('origin', 'Other', 99),
            
            # Transport Networks
            ('region_loop', 'North Region', 1),
            ('region_loop', 'South Region', 2),
            ('region_loop', 'East Region', 3),
            ('region_loop', 'West Region', 4),
            ('region_loop', 'Central Loop', 5),
            ('region_loop', 'Metro Loop 1', 6),
            ('region_loop', 'Metro Loop 2', 7),
            
            ('system_capacity', 'STM-1 (155 Mbps)', 1),
            ('system_capacity', 'STM-4 (622 Mbps)', 2),
            ('system_capacity', 'STM-16 (2.5 Gbps)', 3),
            ('system_capacity', 'STM-64 (10 Gbps)', 4),
            ('system_capacity', '10GE', 5),
            ('system_capacity', '40GE', 6),
            ('system_capacity', '100GE', 7),
            
            ('dot_states', 'Adrar', 1),
            ('dot_states', 'Chlef', 2),
            ('dot_states', 'Laghouat', 3),
            ('dot_states', 'Oum El Bouaghi', 4),
            ('dot_states', 'Batna', 5),
            ('dot_states', 'Béjaïa', 6),
            ('dot_states', 'Biskra', 7),
            ('dot_states', 'Béchar', 8),
            ('dot_states', 'Blida', 9),
            ('dot_states', 'Bouira', 10),
            ('dot_states', 'Tamanrasset', 11),
            ('dot_states', 'Tébessa', 12),
            ('dot_states', 'Tlemcen', 13),
            ('dot_states', 'Tiaret', 14),
            ('dot_states', 'Tizi Ouzou', 15),
            ('dot_states', 'Alger', 16),
            ('dot_states', 'Djelfa', 17),
            ('dot_states', 'Jijel', 18),
            ('dot_states', 'Sétif', 19),
            ('dot_states', 'Saïda', 20),
            
            # Wilayas for File Access and Radio Access Networks
            ('wilayas', 'Adrar', 1),
            ('wilayas', 'Chlef', 2),
            ('wilayas', 'Laghouat', 3),
            ('wilayas', 'Oum El Bouaghi', 4),
            ('wilayas', 'Batna', 5),
            ('wilayas', 'Béjaïa', 6),
            ('wilayas', 'Biskra', 7),
            ('wilayas', 'Béchar', 8),
            ('wilayas', 'Blida', 9),
            ('wilayas', 'Bouira', 10),
            ('wilayas', 'Tamanrasset', 11),
            ('wilayas', 'Tébessa', 12),
            ('wilayas', 'Tlemcen', 13),
            ('wilayas', 'Tiaret', 14),
            ('wilayas', 'Tizi Ouzou', 15),
            ('wilayas', 'Alger', 16),
            ('wilayas', 'Djelfa', 17),
            ('wilayas', 'Jijel', 18),
            ('wilayas', 'Sétif', 19),
            ('wilayas', 'Saïda', 20),
            ('wilayas', 'Skikda', 21),
            ('wilayas', 'Sidi Bel Abbès', 22),
            ('wilayas', 'Annaba', 23),
            ('wilayas', 'Guelma', 24),
            ('wilayas', 'Constantine', 25),
            ('wilayas', 'Médéa', 26),
            ('wilayas', 'Mostaganem', 27),
            ('wilayas', 'MSila', 28),
            ('wilayas', 'Mascara', 29),
            ('wilayas', 'Ouargla', 30),
            ('wilayas', 'Oran', 31),
            ('wilayas', 'El Bayadh', 32),
            ('wilayas', 'Illizi', 33),
            ('wilayas', 'Bordj Bou Arréridj', 34),
            ('wilayas', 'Boumerdès', 35),
            ('wilayas', 'El Tarf', 36),
            ('wilayas', 'Tindouf', 37),
            ('wilayas', 'Tissemsilt', 38),
            ('wilayas', 'El Oued', 39),
            ('wilayas', 'Khenchela', 40),
            ('wilayas', 'Souk Ahras', 41),
            ('wilayas', 'Tipaza', 42),
            ('wilayas', 'Mila', 43),
            ('wilayas', 'Aïn Defla', 44),
            ('wilayas', 'Naâma', 45),
            ('wilayas', 'Aïn Témouchent', 46),
            ('wilayas', 'Ghardaïa', 47),
            ('wilayas', 'Relizane', 48),
            
            # Core Networks
            ('platforms', 'Core Platform 1', 1),
            ('platforms', 'Core Platform 2', 2),
            ('platforms', 'Metro Platform A', 3),
            ('platforms', 'Metro Platform B', 4),
            ('platforms', 'Access Platform 1', 5),
            ('platforms', 'Access Platform 2', 6),
            ('platforms', 'Backbone Platform', 7),
            ('platforms', 'Regional Platform', 8),
            
            ('region_nodes', 'Node-ALG-01 (Algiers Central)', 1),
            ('region_nodes', 'Node-ORA-01 (Oran Main)', 2),
            ('region_nodes', 'Node-CST-01 (Constantine)', 3),
            ('region_nodes', 'Node-ANN-01 (Annaba)', 4),
            ('region_nodes', 'Node-SET-01 (Sétif)', 5),
            ('region_nodes', 'Node-TLM-01 (Tlemcen)', 6),
            ('region_nodes', 'Node-BJA-01 (Béjaïa)', 7),
            ('region_nodes', 'Node-SKD-01 (Skikda)', 8),
            ('region_nodes', 'Node-GHR-01 (Ghardaïa)', 9),
            ('region_nodes', 'Node-OUR-01 (Ouargla)', 10),
            
            # Backbone Internet Networks
            ('interconnect_types', 'BGP Peering', 1),
            ('interconnect_types', 'Transit Link', 2),
            ('interconnect_types', 'IXP Connection', 3),
            ('interconnect_types', 'Satellite Link', 4),
            ('interconnect_types', 'Submarine Cable', 5),
            ('interconnect_types', 'Terrestrial Link', 6),
            ('interconnect_types', 'MPLS VPN', 7),
            ('interconnect_types', 'Direct Connect', 8),
            
            ('platform_igws', 'IGW-ALG-01 (Algiers Gateway)', 1),
            ('platform_igws', 'IGW-ORA-01 (Oran Gateway)', 2),
            ('platform_igws', 'IGW-CST-01 (Constantine Gateway)', 3),
            ('platform_igws', 'IGW-ANN-01 (Annaba Gateway)', 4),
            ('platform_igws', 'Platform-INT-01 (International)', 5),
            ('platform_igws', 'Platform-SAT-01 (Satellite)', 6),
            ('platform_igws', 'Platform-SUB-01 (Submarine)', 7),
            ('platform_igws', 'Platform-TER-01 (Terrestrial)', 8),
        ]
        
        created_count = 0
        updated_count = 0
        
        for category, value, sort_order in sample_data:
            obj, created = DropdownConfiguration.objects.get_or_create(
                category=category,
                value=value,
                defaults={
                    'is_active': True,
                    'sort_order': sort_order
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created: {category} - {value}')
            else:
                # Update sort order if different
                if obj.sort_order != sort_order:
                    obj.sort_order = sort_order
                    obj.save()
                    updated_count += 1
                    self.stdout.write(f'Updated: {category} - {value}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated dropdown data! '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )