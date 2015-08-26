# -*- coding: utf-8 -*-
"""
"""
import os
import imp
import unittest

test_utils = imp.load_source( 'test_utils',
    os.path.join( os.path.dirname( __file__), '../unittest_utils/utility.py' ) )

from galaxy import eggs
eggs.require( 'SQLAlchemy >= 0.4' )
import sqlalchemy

from galaxy import model
from galaxy import exceptions

from base import BaseTestCase

from galaxy.managers.datasets import (
    DatasetManager, DatasetRBACPermissions, DatasetSerializer, DatasetDeserializer )

from galaxy.managers.datasets import DatasetAssociationManager
from galaxy.managers.histories import HistoryManager
from galaxy.managers.hdas import HDAManager


# =============================================================================
default_password = '123456'
user2_data = dict( email='user2@user2.user2', username='user2', password=default_password )
user3_data = dict( email='user3@user3.user3', username='user3', password=default_password )


# =============================================================================
class DatasetManagerTestCase( BaseTestCase ):

    def set_up_managers( self ):
        super( DatasetManagerTestCase, self ).set_up_managers()
        self.dataset_manager = DatasetManager( self.app )

    def test_create( self ):
        self.log( "should be able to create a new Dataset" )
        dataset1 = self.dataset_manager.create()
        self.assertIsInstance( dataset1, model.Dataset )
        self.assertEqual( dataset1, self.trans.sa_session.query( model.Dataset ).get( dataset1.id ) )

    def test_base( self ):
        dataset1 = self.dataset_manager.create()
        dataset2 = self.dataset_manager.create()

        self.log( "should be able to query" )
        datasets = self.trans.sa_session.query( model.Dataset ).all()
        self.assertEqual( self.dataset_manager.list(), datasets )
        self.assertEqual( self.dataset_manager.one( filters=( model.Dataset.id == dataset1.id ) ), dataset1 )
        self.assertEqual( self.dataset_manager.by_id( dataset1.id ), dataset1 )
        self.assertEqual( self.dataset_manager.by_ids( [ dataset2.id, dataset1.id ] ), [ dataset2, dataset1 ] )

        self.log( "should be able to limit and offset" )
        self.assertEqual( self.dataset_manager.list( limit=1 ), datasets[0:1] )
        self.assertEqual( self.dataset_manager.list( offset=1 ), datasets[1:] )
        self.assertEqual( self.dataset_manager.list( limit=1, offset=1 ), datasets[1:2] )

        self.assertEqual( self.dataset_manager.list( limit=0 ), [] )
        self.assertEqual( self.dataset_manager.list( offset=3 ), [] )

        self.log( "should be able to order" )
        self.assertEqual( self.dataset_manager.list( order_by=sqlalchemy.desc( model.Dataset.create_time ) ),
            [ dataset2, dataset1 ] )

    def test_delete( self ):
        item1 = self.dataset_manager.create()

        self.log( "should be able to delete and undelete a dataset" )
        self.assertFalse( item1.deleted )
        self.assertEqual( self.dataset_manager.delete( item1 ), item1 )
        self.assertTrue( item1.deleted )
        self.assertEqual( self.dataset_manager.undelete( item1 ), item1 )
        self.assertFalse( item1.deleted )

    def test_purge_allowed( self ):
        self.trans.app.config.allow_user_dataset_purge = True
        item1 = self.dataset_manager.create()

        self.log( "should purge a dataset if config does allow" )
        self.assertFalse( item1.purged )
        self.assertEqual( self.dataset_manager.purge( item1 ), item1 )
        self.assertTrue( item1.purged )

        self.log( "should delete a dataset when purging" )
        self.assertTrue( item1.deleted )

    def test_purge_not_allowed( self ):
        self.trans.app.config.allow_user_dataset_purge = False
        item1 = self.dataset_manager.create()

        self.log( "should raise an error when purging a dataset if config does not allow" )
        self.assertFalse( item1.purged )
        self.assertRaises( exceptions.ConfigDoesNotAllowException, self.dataset_manager.purge, item1 )
        self.assertFalse( item1.purged )

    def test_create_with_no_permissions( self ):
        self.log( "should be able to create a new Dataset without any permissions" )
        dataset = self.dataset_manager.create()

        permissions = self.dataset_manager.permissions.get( dataset )
        self.assertIsInstance( permissions, tuple )
        self.assertEqual( len( permissions ), 2 )
        manage_permissions, access_permissions = permissions
        self.assertEqual( manage_permissions, [] )
        self.assertEqual( access_permissions, [] )

        user3 = self.user_manager.create( **user3_data )
        self.log( "a dataset without permissions shouldn't be manageable to just anyone" )
        self.assertFalse( self.dataset_manager.permissions.manage.is_permitted( dataset, user3 ) )
        self.log( "a dataset without permissions should be accessible" )
        self.assertTrue( self.dataset_manager.permissions.access.is_permitted( dataset, user3 ) )

    def test_create_public_dataset( self ):
        self.log( "should be able to create a new Dataset and give it some permissions that actually, you know, might work if there's any justice in this universe" )
        owner = self.user_manager.create( **user2_data )
        owner_private_role = self.user_manager.private_role( owner )
        dataset = self.dataset_manager.create( manage_roles=[ owner_private_role ] )

        permissions = self.dataset_manager.permissions.get( dataset )
        self.assertIsInstance( permissions, tuple )
        self.assertEqual( len( permissions ), 2 )
        manage_permissions, access_permissions = permissions
        self.assertIsInstance( manage_permissions, list )
        self.assertIsInstance( manage_permissions[0], model.DatasetPermissions )
        self.assertEqual( access_permissions, [] )

        user3 = self.user_manager.create( **user3_data )
        self.log( "a public dataset should be manageable to it's owner" )
        self.assertTrue( self.dataset_manager.permissions.manage.is_permitted( dataset, owner ) )
        self.log( "a public dataset shouldn't be manageable to just anyone" )
        self.assertFalse( self.dataset_manager.permissions.manage.is_permitted( dataset, user3 ) )
        self.log( "a public dataset should be accessible" )
        self.assertTrue( self.dataset_manager.permissions.access.is_permitted( dataset, user3 ) )

    def test_create_private_dataset( self ):
        self.log( "should be able to create a new Dataset and give it some permissions that actually, you know, might work if there's any justice in this universe" )
        owner = self.user_manager.create( **user2_data )
        owner_private_role = self.user_manager.private_role( owner )
        dataset = self.dataset_manager.create(
            manage_roles=[ owner_private_role ], access_roles=[ owner_private_role ] )

        permissions = self.dataset_manager.permissions.get( dataset )
        self.assertIsInstance( permissions, tuple )
        self.assertEqual( len( permissions ), 2 )
        manage_permissions, access_permissions = permissions
        self.assertIsInstance( manage_permissions, list )
        self.assertIsInstance( manage_permissions[0], model.DatasetPermissions )
        self.assertIsInstance( access_permissions, list )
        self.assertIsInstance( access_permissions[0], model.DatasetPermissions )

        self.log( "a private dataset should be manageable by it's owner" )
        self.assertTrue( self.dataset_manager.permissions.manage.is_permitted( dataset, owner ) )
        self.log( "a private dataset should be accessible to it's owner" )
        self.assertTrue( self.dataset_manager.permissions.access.is_permitted( dataset, owner ) )

        user3 = self.user_manager.create( **user3_data )
        self.log( "a private dataset shouldn't be manageable to just anyone" )
        self.assertFalse( self.dataset_manager.permissions.manage.is_permitted( dataset, user3 ) )
        self.log( "a private dataset shouldn't be accessible to just anyone" )
        self.assertFalse( self.dataset_manager.permissions.access.is_permitted( dataset, user3 ) )


# =============================================================================
class DatasetRBACPermissionsTestCase( BaseTestCase ):

    def set_up_managers( self ):
        super( DatasetRBACPermissionsTestCase, self ).set_up_managers()
        self.dataset_manager = DatasetManager( self.app )

    # def test_manage( self ):
    #     self.log( "should be able to create a new Dataset" )
    #     dataset1 = self.dataset_manager.create()
    #     self.assertIsInstance( dataset1, model.Dataset )
    #     self.assertEqual( dataset1, self.app.model.context.query( model.Dataset ).get( dataset1.id ) )
    #


# =============================================================================
# web.url_for doesn't work well in the framework
testable_url_for = lambda *a, **k: '(fake url): %s, %s' % ( a, k )
DatasetSerializer.url_for = staticmethod( testable_url_for )

class DatasetSerializerTestCase( BaseTestCase ):

    def set_up_managers( self ):
        super( DatasetSerializerTestCase, self ).set_up_managers()
        self.dataset_manager = DatasetManager( self.app )
        self.dataset_serializer = DatasetSerializer( self.app )

    def test_views( self ):
        dataset = self.dataset_manager.create()

        self.log( 'should have a summary view' )
        summary_view = self.dataset_serializer.serialize_to_view( dataset, view='summary' )
        self.assertKeys( summary_view, self.dataset_serializer.views[ 'summary' ] )

        self.log( 'should have the summary view as default view' )
        default_view = self.dataset_serializer.serialize_to_view( dataset, default_view='summary' )
        self.assertKeys( summary_view, self.dataset_serializer.views[ 'summary' ] )

        self.log( 'should have a serializer for all serializable keys' )
        for key in self.dataset_serializer.serializable_keyset:
            instantiated_attribute = getattr( dataset, key, None )
            if not ( ( key in self.dataset_serializer.serializers )
                  or ( isinstance( instantiated_attribute, self.TYPES_NEEDING_NO_SERIALIZERS ) ) ):
                self.fail( 'no serializer for: %s (%s)' % ( key, instantiated_attribute ) )
        else:
            self.assertTrue( True, 'all serializable keys have a serializer' )

    def test_views_and_keys( self ):
        dataset = self.dataset_manager.create()

        self.log( 'should be able to use keys with views' )
        serialized = self.dataset_serializer.serialize_to_view( dataset,
            view='summary', keys=[ 'permissions' ] )
        self.assertKeys( serialized,
            self.dataset_serializer.views[ 'summary' ] + [ 'permissions' ] )

        self.log( 'should be able to use keys on their own' )
        serialized = self.dataset_serializer.serialize_to_view( dataset,
            keys=[ 'purgable', 'file_size' ] )
        self.assertKeys( serialized, [ 'purgable', 'file_size' ] )

    def test_serialize_permissions( self ):
        dataset = self.dataset_manager.create()
        self.log( 'serialized permissions should be well formed' )

    def test_serializers( self ):
        user2 = self.user_manager.create( **user2_data )
        dataset = self.dataset_manager.create()
        all_keys = list( self.dataset_serializer.serializable_keyset )
        serialized = self.dataset_serializer.serialize( dataset, all_keys )

        self.log( 'everything serialized should be of the proper type' )
        self.assertEncodedId( serialized[ 'id' ] )
        self.assertDate( serialized[ 'create_time' ] )
        self.assertDate( serialized[ 'update_time' ] )

        self.assertUUID( serialized[ 'uuid' ] )
        self.assertIsInstance( serialized[ 'state' ], basestring )
        self.assertIsInstance( serialized[ 'deleted' ], bool )
        self.assertIsInstance( serialized[ 'purged' ], bool )
        self.assertIsInstance( serialized[ 'purgable' ], bool )

        # # TODO: no great way to do these with mocked dataset
        # self.assertIsInstance( serialized[ 'file_size' ], int )
        # self.assertIsInstance( serialized[ 'total_size' ], int )

        self.log( 'serialized should jsonify well' )
        self.assertIsJsonifyable( serialized )


# =============================================================================
class DatasetDeserializerTestCase( BaseTestCase ):

    def set_up_managers( self ):
        super( DatasetDeserializerTestCase, self ).set_up_managers()
        self.dataset_manager = DatasetManager( self.app )
        self.dataset_deserializer = DatasetDeserializer( self.app )

    def test_deserialize_delete( self ):
        dataset = self.dataset_manager.create()

        self.log( 'should raise when deserializing deleted from non-bool' )
        self.assertFalse( dataset.deleted )
        self.assertRaises( exceptions.RequestParameterInvalidException,
            self.dataset_deserializer.deserialize, dataset, data={ 'deleted': None } )
        self.assertFalse( dataset.deleted )
        self.log( 'should be able to deserialize deleted from True' )
        self.dataset_deserializer.deserialize( dataset, data={ 'deleted': True } )
        self.assertTrue( dataset.deleted )
        self.log( 'should be able to reverse by deserializing deleted from False' )
        self.dataset_deserializer.deserialize( dataset, data={ 'deleted': False } )
        self.assertFalse( dataset.deleted )

    def test_deserialize_purge( self ):
        dataset = self.dataset_manager.create()

        self.log( 'should raise when deserializing purged from non-bool' )
        self.assertRaises( exceptions.RequestParameterInvalidException,
            self.dataset_deserializer.deserialize, dataset, data={ 'purged': None } )
        self.assertFalse( dataset.purged )
        self.log( 'should be able to deserialize purged from True' )
        self.dataset_deserializer.deserialize( dataset, data={ 'purged': True } )
        self.assertTrue( dataset.purged )
        # TODO: should this raise an error?
        self.log( 'should NOT be able to deserialize purged from False (will remain True)' )
        self.dataset_deserializer.deserialize( dataset, data={ 'purged': False } )
        self.assertTrue( dataset.purged )

    # def test_deserialize_permissions( self ):
    #     pass


# =============================================================================
# NOTE: that we test the DatasetAssociation* classes in either test_HDAManager or test_LDAManager
# (as part of those subclasses):
#   DatasetAssociationManager,
#   DatasetAssociationSerializer,
#   DatasetAssociationDeserializer,
#   DatasetAssociationFilterParser

# =============================================================================
if __name__ == '__main__':
    # or more generally, nosetests test_resourcemanagers.py -s -v
    unittest.main()
